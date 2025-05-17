import git
import json
import sqlite3
import os
from datetime import datetime, timezone

# --- Database Setup ---
DB_NAME = "fires.sqlite"

def init_db():
    """Initializes the SQLite database and creates tables if they don't exist."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Table to store the latest known state and key historical points of each fire
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS fires (
        fire_id TEXT PRIMARY KEY,
        lat REAL,
        lng REAL,
        location TEXT,
        district TEXT,
        concelho TEXT,
        freguesia TEXT,
        natureza TEXT,
        first_seen_commit_hash TEXT,
        first_seen_data_timestamp INTEGER, -- Unix timestamp from original data 'dateTime.sec'
        last_updated_commit_hash TEXT,   -- Commit where this fire's data was last changed or confirmed
        last_updated_data_timestamp INTEGER, -- Unix timestamp from original data 'updated.sec'
        is_currently_active BOOLEAN      -- Based on the 'active' flag in the latest data for this fire
    )
    ''')

    # Table to log all changes, appearances, and disappearances of each fire
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS fire_updates (
        update_id INTEGER PRIMARY KEY AUTOINCREMENT,
        fire_id TEXT,
        commit_hash TEXT,
        commit_timestamp INTEGER,          -- Unix timestamp of the commit
        data_timestamp INTEGER,            -- Unix timestamp from 'updated.sec' or 'dateTime.sec' in the fire data
        status TEXT,
        status_code INTEGER,
        man INTEGER,
        terrain INTEGER,
        aerial INTEGER,
        meios_aquaticos INTEGER,
        active_in_commit BOOLEAN,          -- 'active' flag from the JSON in this commit
        change_type TEXT,                  -- 'NEW', 'UPDATED', 'DISAPPEARED'
        raw_data TEXT,                     -- Full JSON data for this fire in this commit
        FOREIGN KEY (fire_id) REFERENCES fires(fire_id)
    )
    ''')
    conn.commit()
    return conn

# --- Git Processing ---

def get_file_content_at_commit(repo, commit_hexsha, file_path_in_repo):
    """
    Retrieves the content of a file from a specific commit.
    Returns None if the file doesn't exist in that commit or an error occurs.
    """
    try:
        commit_obj = repo.commit(commit_hexsha)
        # Split the file_path_in_repo in case it contains directories
        path_parts = file_path_in_repo.strip('/').split('/')
        current_tree_item = commit_obj.tree
        for part in path_parts:
            current_tree_item = current_tree_item[part] # This can raise KeyError if part not found
        
        # current_tree_item is now a blob
        return current_tree_item.data_stream.read().decode('utf-8')
    except (git.exc.GitCommandError, KeyError, AttributeError) as e:
        # print(f"Debug: Could not read file {file_path_in_repo} at commit {commit_hexsha[:7]}: {e}")
        return None

def parse_fire_data(json_content):
    """
    Parses JSON content into a dictionary of fire data, keyed by fire ID.
    Returns an empty dictionary if parsing fails or structure is unexpected.
    """
    if not json_content:
        return {}
    try:
        data = json.loads(json_content)
        if data.get("success") and isinstance(data.get("data"), list):
            # Ensure items in data['data'] are dictionaries and have an 'id'
            fires_map = {
                item['id']: item for item in data['data']
                if isinstance(item, dict) and 'id' in item
            }
            return fires_map
        else:
            # print(f"Warning: JSON structure not as expected (missing 'success' or 'data' list).")
            return {}
    except json.JSONDecodeError as e:
        # print(f"Warning: JSON decoding error: {e} for content: {json_content[:100]}")
        return {}
    except TypeError as e:
        # print(f"Warning: TypeError during JSON processing (e.g. item not a dict): {e}")
        return {}


def compare_fire_data_are_different(old_data, new_data):
    """
    Compares two fire data dictionaries for meaningful differences.
    Returns True if relevant fields are different, False otherwise.
    """
    if not old_data or not new_data: # Should only happen if old_data is for a new fire
        return True 

    # Fields that define an update if they change.
    # 'active' is crucial. 'updated.sec' changing also signifies an update from source.
    relevant_fields = [
        'lat', 'lng', 'location', 'man', 'terrain', 'aerial', 'meios_aquaticos',
        'status', 'statusCode', 'natureza', 'active', 'localidade', 'important',
        'district', 'concelho', 'freguesia', 'naturezaCode', 'statusColor',
        # Add other fields from your JSON that you consider important for tracking changes.
    ]
    for field in relevant_fields:
        if old_data.get(field) != new_data.get(field):
            return True

    # Specifically check the 'updated' timestamp if it exists
    if old_data.get('updated', {}).get('sec') != new_data.get('updated', {}).get('sec'):
        return True
        
    # If 'updated' is not present, but 'dateTime' is, and it changed (though less likely for existing fire)
    if 'updated' not in old_data and 'updated' not in new_data:
        if old_data.get('dateTime', {}).get('sec') != new_data.get('dateTime', {}).get('sec'):
            return True
            
    return False

# --- Main Logic ---
def process_repository(repo_path, json_file_path_in_repo):
    """
    Main function to process the Git repository, analyze fire data from JSON files in commits,
    and store the history in an SQLite database.
    """
    conn = init_db()
    cursor = conn.cursor()

    try:
        repo = git.Repo(repo_path)
    except git.exc.InvalidGitRepositoryError:
        print(f"Error: Path '{repo_path}' is not a valid Git repository.")
        return
    except git.exc.NoSuchPathError:
        print(f"Error: Repository path '{repo_path}' does not exist.")
        return

    # Get commits in chronological order (oldest to newest)
    commits = list(repo.iter_commits(reverse=True))
    if not commits:
        print("No commits found in the repository.")
        conn.close()
        return

    print(f"Processing {len(commits)} commits...")

    # In-memory state tracker for the last known data of each fire_id.
    # Key: fire_id, Value: dict of the fire data from JSON
    last_known_fire_states = {}

    for i, commit in enumerate(commits):
        commit_hash = commit.hexsha
        # Ensure commit.committed_datetime is offset-aware before calling timestamp()
        commit_dt_aware = commit.committed_datetime
        if commit_dt_aware.tzinfo is None or commit_dt_aware.tzinfo.utcoffset(commit_dt_aware) is None:
            commit_dt_aware = commit_dt_aware.replace(tzinfo=timezone.utc) # Assume UTC if naive
        commit_timestamp = int(commit_dt_aware.timestamp())

        # print(f"\nProcessing commit {i+1}/{len(commits)}: {commit_hash[:7]} ({commit.committed_datetime})")

        json_content = get_file_content_at_commit(repo, commit_hash, json_file_path_in_repo)
        current_commit_fires_map = parse_fire_data(json_content)

        if not json_content and not current_commit_fires_map :
            # print(f"  No valid fire data file '{json_file_path_in_repo}' in commit {commit_hash[:7]}.")
            # Disappearance logic below will handle fires that were active and are now gone.
            pass

        processed_fire_ids_in_this_commit = set()

        # 1. Process fires present in the current commit's JSON
        for fire_id, current_fire_data in current_commit_fires_map.items():
            processed_fire_ids_in_this_commit.add(fire_id)
            previous_fire_data_state = last_known_fire_states.get(fire_id)

            # Prepare data for the fire_updates table
            update_log_entry = {
                'fire_id': fire_id,
                'commit_hash': commit_hash,
                'commit_timestamp': commit_timestamp,
                'data_timestamp': current_fire_data.get('updated', {}).get('sec') or \
                                  current_fire_data.get('dateTime', {}).get('sec'),
                'status': current_fire_data.get('status'),
                'status_code': current_fire_data.get('statusCode'),
                'man': current_fire_data.get('man'),
                'terrain': current_fire_data.get('terrain'),
                'aerial': current_fire_data.get('aerial'),
                'meios_aquaticos': current_fire_data.get('meios_aquaticos'),
                'active_in_commit': current_fire_data.get('active', False),
                'raw_data': json.dumps(current_fire_data)
            }

            if not previous_fire_data_state:
                # This is a new fire never seen before by the script
                # print(f"  NEW fire: {fire_id}")
                cursor.execute('''
                    INSERT INTO fires (fire_id, lat, lng, location, district, concelho, freguesia, natureza,
                                     first_seen_commit_hash, first_seen_data_timestamp,
                                     last_updated_commit_hash, last_updated_data_timestamp, is_currently_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (fire_id, current_fire_data.get('lat'), current_fire_data.get('lng'),
                      current_fire_data.get('location'), current_fire_data.get('district'),
                      current_fire_data.get('concelho'), current_fire_data.get('freguesia'),
                      current_fire_data.get('natureza'), commit_hash,
                      current_fire_data.get('dateTime', {}).get('sec'), # first_seen_data_timestamp
                      commit_hash, current_fire_data.get('updated', {}).get('sec'), # last_updated
                      current_fire_data.get('active', False)))
                
                update_log_entry['change_type'] = 'NEW'
                cursor.execute('''
                    INSERT INTO fire_updates (fire_id, commit_hash, commit_timestamp, data_timestamp, status, status_code,
                                            man, terrain, aerial, meios_aquaticos, active_in_commit, change_type, raw_data)
                    VALUES (:fire_id, :commit_hash, :commit_timestamp, :data_timestamp, :status, :status_code,
                            :man, :terrain, :aerial, :meios_aquaticos, :active_in_commit, :change_type, :raw_data)
                ''', update_log_entry)
            else:
                # Existing fire, check if its data or active status has changed
                if compare_fire_data_are_different(previous_fire_data_state, current_fire_data):
                    # print(f"  UPDATED fire: {fire_id}")
                    cursor.execute('''
                        UPDATE fires
                        SET lat = ?, lng = ?, location = ?, district = ?, concelho = ?, freguesia = ?, natureza = ?,
                            last_updated_commit_hash = ?, last_updated_data_timestamp = ?, is_currently_active = ?
                        WHERE fire_id = ?
                    ''', (current_fire_data.get('lat'), current_fire_data.get('lng'),
                          current_fire_data.get('location'), current_fire_data.get('district'),
                          current_fire_data.get('concelho'), current_fire_data.get('freguesia'),
                          current_fire_data.get('natureza'), commit_hash,
                          current_fire_data.get('updated', {}).get('sec'),
                          current_fire_data.get('active', False), fire_id))
                    
                    update_log_entry['change_type'] = 'UPDATED'
                    cursor.execute('''
                        INSERT INTO fire_updates (fire_id, commit_hash, commit_timestamp, data_timestamp, status, status_code,
                                                man, terrain, aerial, meios_aquaticos, active_in_commit, change_type, raw_data)
                        VALUES (:fire_id, :commit_hash, :commit_timestamp, :data_timestamp, :status, :status_code,
                                :man, :terrain, :aerial, :meios_aquaticos, :active_in_commit, :change_type, :raw_data)
                    ''', update_log_entry)
                else:
                    # Fire data is identical to the last known state.
                    # Only update 'last_updated_commit_hash' in 'fires' to show it's still confirmed in this commit.
                    # No new entry in 'fire_updates' as there's no change to log.
                    # print(f"  UNCHANGED (still present) fire: {fire_id}")
                    cursor.execute('''
                        UPDATE fires SET last_updated_commit_hash = ? WHERE fire_id = ?
                    ''', (commit_hash, fire_id))

            # Update the in-memory state for this fire
            last_known_fire_states[fire_id] = current_fire_data

        # 2. Process fires that were known (and active) but are NOT in the current commit's JSON (disappeared)
        previously_known_fire_ids = set(last_known_fire_states.keys())
        disappeared_fire_ids = previously_known_fire_ids - processed_fire_ids_in_this_commit

        for fire_id in disappeared_fire_ids:
            last_data = last_known_fire_states[fire_id]
            # Consider it "disappeared" if it was marked as active in our state tracker
            if last_data.get('active', False):
                # print(f"  DISAPPEARED fire: {fire_id}")
                cursor.execute('''
                    UPDATE fires
                    SET is_currently_active = ?, last_updated_commit_hash = ?
                    WHERE fire_id = ?
                ''', (False, commit_hash, fire_id)) # Mark inactive, update commit hash of this observation

                # Log this disappearance event in fire_updates
                disappeared_log_entry = {
                    'fire_id': fire_id,
                    'commit_hash': commit_hash,
                    'commit_timestamp': commit_timestamp,
                    'data_timestamp': commit_timestamp, # Use commit time as no specific fire data point
                    'status': "Disappeared from source",
                    'status_code': None, # Or a custom code for disappearance
                    'man': last_data.get('man'), # Log last known values
                    'terrain': last_data.get('terrain'),
                    'aerial': last_data.get('aerial'),
                    'meios_aquaticos': last_data.get('meios_aquaticos'),
                    'active_in_commit': False, # Not active as it's not in the commit's data
                    'change_type': 'DISAPPEARED',
                    'raw_data': json.dumps(last_data) # Store the last known state
                }
                cursor.execute('''
                    INSERT INTO fire_updates (fire_id, commit_hash, commit_timestamp, data_timestamp, status, status_code,
                                            man, terrain, aerial, meios_aquaticos, active_in_commit, change_type, raw_data)
                    VALUES (:fire_id, :commit_hash, :commit_timestamp, :data_timestamp, :status, :status_code,
                            :man, :terrain, :aerial, :meios_aquaticos, :active_in_commit, :change_type, :raw_data)
                ''', disappeared_log_entry)

            # Update the in-memory state: mark as inactive because it's gone from the current file
            if fire_id in last_known_fire_states: # Should always be true
                 last_known_fire_states[fire_id]['active'] = False


        # Commit to DB periodically or at the end
        if (i + 1) % 100 == 0 or (i + 1) == len(commits):
            conn.commit()
            print(f"Processed and committed {i+1}/{len(commits)} commits.")

    conn.commit() # Final commit of any remaining transactions
    conn.close()
    print(f"Processing complete. Database saved to '{DB_NAME}'.")

if __name__ == "__main__":
    process_repository("./", "fogos.json")
