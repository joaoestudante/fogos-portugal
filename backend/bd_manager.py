import git
import json
import sqlite3
import os
from datetime import datetime, timezone

# --- Database Setup ---
DB_NAME = "fires.sqlite" # Keep the same DB name

# --- Helper Functions (mostly from original, with additions) ---

def init_db():
    """Initializes the SQLite database and creates/updates tables."""
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
        first_seen_data_timestamp INTEGER,
        last_updated_commit_hash TEXT,
        last_updated_data_timestamp INTEGER,
        is_currently_active BOOLEAN
    )
    ''')

    # Table to log all changes, appearances, and disappearances of each fire
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS fire_updates (
        update_id INTEGER PRIMARY KEY AUTOINCREMENT,
        fire_id TEXT,
        commit_hash TEXT,
        commit_timestamp INTEGER,
        data_timestamp INTEGER,
        status TEXT,
        status_code INTEGER,
        man INTEGER,
        terrain INTEGER,
        aerial INTEGER,
        meios_aquaticos INTEGER,
        active_in_commit BOOLEAN,
        change_type TEXT,
        raw_data TEXT,
        FOREIGN KEY (fire_id) REFERENCES fires(fire_id)
    )
    ''')

    # New table to store script metadata, like the last processed commit
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS script_metadata (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    ''')
    conn.commit()
    return conn

def get_last_processed_commit_hash(cursor):
    """Retrieves the hash of the last successfully processed commit."""
    cursor.execute("SELECT value FROM script_metadata WHERE key = 'last_processed_commit_hash'")
    row = cursor.fetchone()
    return row[0] if row else None

def update_last_processed_commit_hash(cursor, commit_hash):
    """Updates the hash of the last successfully processed commit."""
    cursor.execute("INSERT OR REPLACE INTO script_metadata (key, value) VALUES (?, ?)",
                   ('last_processed_commit_hash', commit_hash))

def get_file_content_at_commit(repo, commit_hexsha, file_path_in_repo):
    """Retrieves the content of a file from a specific commit."""
    try:
        commit_obj = repo.commit(commit_hexsha)
        path_parts = file_path_in_repo.strip('/').split('/')
        current_tree_item = commit_obj.tree
        for part in path_parts:
            current_tree_item = current_tree_item[part]
        return current_tree_item.data_stream.read().decode('utf-8')
    except Exception: # Broad exception for simplicity, consider more specific ones
        return None

def parse_fire_data(json_content):
    """Parses JSON content into a dictionary of fire data, keyed by fire ID."""
    if not json_content:
        return {}
    try:
        data = json.loads(json_content)
        if data.get("success") and isinstance(data.get("data"), list):
            return {item['id']: item for item in data['data'] if isinstance(item, dict) and 'id' in item}
        return {}
    except (json.JSONDecodeError, TypeError):
        return {}

def compare_fire_data_are_different(old_data, new_data):
    """Compares two fire data dictionaries for meaningful differences."""
    if not old_data or not new_data:
        return True
    relevant_fields = [
        'lat', 'lng', 'location', 'man', 'terrain', 'aerial', 'meios_aquaticos',
        'status', 'statusCode', 'natureza', 'active', 'localidade', 'important',
        'district', 'concelho', 'freguesia', 'naturezaCode', 'statusColor',
    ]
    for field in relevant_fields:
        if old_data.get(field) != new_data.get(field):
            return True
    if old_data.get('updated', {}).get('sec') != new_data.get('updated', {}).get('sec'):
        return True
    if 'updated' not in old_data and 'updated' not in new_data:
        if old_data.get('dateTime', {}).get('sec') != new_data.get('dateTime', {}).get('sec'):
            return True
    return False

def load_current_fire_states_from_db(repo, conn, json_file_path_in_repo):
    """
    Loads the last known full state of all fires from the database.
    It does this by looking at the `fires` table for `last_updated_commit_hash`,
    then fetching the actual JSON from that commit to reconstruct the full fire data.
    """
    cursor = conn.cursor()
    states = {}
    cursor.execute("SELECT fire_id, last_updated_commit_hash FROM fires")
    fires_in_db = cursor.fetchall()

    if not fires_in_db:
        print("  No existing fire states in DB to load.")
        return states

    print(f"  Loading initial states for {len(fires_in_db)} fires from their last known commits...")
    for fire_id, last_commit_hash in fires_in_db:
        if not last_commit_hash: # Should not happen if data is consistent
            print(f"  Warning: Fire {fire_id} has no last_updated_commit_hash in DB. Skipping.")
            continue

        json_content = get_file_content_at_commit(repo, last_commit_hash, json_file_path_in_repo)
        if json_content:
            fires_map_for_commit = parse_fire_data(json_content)
            if fire_id in fires_map_for_commit:
                states[fire_id] = fires_map_for_commit[fire_id]
            # else:
                # print(f"  Warning: Fire {fire_id} not found in its last_updated_commit_hash ({last_commit_hash[:7]}) content. Its state might be outdated if it disappeared.")
        # else:
            # print(f"  Warning: Could not retrieve content for fire {fire_id} from commit {last_commit_hash[:7]}.")
    print(f"  Finished loading initial states. {len(states)} states loaded.")
    return states

# --- Main Incremental Logic ---
def process_repository_incrementally(repo_path, json_file_path_in_repo):
    """
    Processes new Git commits since the last run, updating the fire data database.
    """
    conn = init_db()
    cursor = conn.cursor()

    try:
        repo = git.Repo(repo_path)
    except git.exc.InvalidGitRepositoryError:
        print(f"Error: Path '{repo_path}' is not a valid Git repository.")
        conn.close()
        return
    except git.exc.NoSuchPathError:
        print(f"Error: Repository path '{repo_path}' does not exist.")
        conn.close()
        return

    last_processed_hash = get_last_processed_commit_hash(cursor)
    head_commit_hash = repo.head.commit.hexsha

    if last_processed_hash == head_commit_hash:
        print(f"No new commits since last run (last processed: {last_processed_hash[:7]}). Database is up-to-date.")
        conn.close()
        return

    commits_to_process = []
    if last_processed_hash:
        print(f"Last processed commit: {last_processed_hash[:7]}. Looking for new commits up to HEAD ({head_commit_hash[:7]}).")
        # Iterate from the commit *after* last_processed_hash up to HEAD
        # The range last_processed_hash..HEAD means "commits reachable from HEAD but not from last_processed_hash"
        # reverse=True gives oldest new commit first.
        try:
            commits_to_process = list(repo.iter_commits(rev=f"{last_processed_hash}..{head_commit_hash}", reverse=True))
        except git.exc.GitCommandError as e:
            print(f"Error fetching commits: {e}. This might happen if last_processed_hash is no longer in main branch (e.g., due to a force push/rebase).")
            print("Consider resetting last_processed_commit_hash or running a full rebuild.")
            # Fallback: process all commits if range fails and DB might be empty/old
            # Or prompt user, or have a flag for full rebuild
            # For now, we'll assume this means we need to start fresh if there's a problem.
            # A safer fallback for production might be to just process the last N commits.
            # Or, if this error occurs, clear `last_processed_hash` and re-run for full history.
            # For this script, let's try processing all if `last_processed_hash` is problematic or not found.
            # This can happen if the history was rewritten.
            print(f"Warning: Could not find commit range. Checking if '{last_processed_hash}' exists.")
            try:
                repo.commit(last_processed_hash) # Check if it exists
                # If it exists but range failed, it's unusual.
            except git.exc.BadName: # Commit doesn't exist anymore
                print(f"Commit {last_processed_hash} not found. Repository history might have changed. Consider a full rebuild or resetting metadata.")
                print("Attempting to process all commits instead (this will be slow if DB is large and not empty).")
                last_processed_hash = None # Force full scan
                commits_to_process = list(repo.iter_commits(reverse=True))

    if not last_processed_hash: # First run or forced full scan
        print("No last processed commit found or full scan forced. Processing all commits...")
        commits_to_process = list(repo.iter_commits(reverse=True))

    if not commits_to_process:
        # This can happen if last_processed_hash was HEAD, or if the repo is empty
        # The check `last_processed_hash == head_commit_hash` should catch the "up-to-date" case.
        # If repo is empty or only has one commit which was processed.
        current_repo_commits = list(repo.iter_commits())
        if not current_repo_commits:
             print("No commits found in the repository.")
        else:
            print("No new commits to process.")
        conn.close()
        return

    print(f"Found {len(commits_to_process)} new commits to process.")

    # Load the state of fires as they were at the end of the previous run
    # This forms the baseline for comparison for the new commits.
    # This map will be updated *during* the processing of new commits.
    print("Loading current fire states from database (based on their last update)...")
    # This is our "snapshot" of the world *before* these new commits are applied.
    # The values in this map are full fire data dicts.
    in_memory_fire_states = load_current_fire_states_from_db(repo, conn, json_file_path_in_repo)
    
    newest_commit_processed_in_this_run = None

    for i, commit in enumerate(commits_to_process):
        commit_hash = commit.hexsha
        commit_dt_aware = commit.committed_datetime
        if commit_dt_aware.tzinfo is None or commit_dt_aware.tzinfo.utcoffset(commit_dt_aware) is None:
            commit_dt_aware = commit_dt_aware.replace(tzinfo=timezone.utc)
        commit_timestamp = int(commit_dt_aware.timestamp())

        print(f"\nProcessing new commit {i+1}/{len(commits_to_process)}: {commit_hash[:7]} ({commit.committed_datetime})")

        json_content = get_file_content_at_commit(repo, commit_hash, json_file_path_in_repo)
        current_commit_fires_map = parse_fire_data(json_content) # Fires present in THIS commit's JSON

        if not json_content and not current_commit_fires_map:
            print(f"  No valid fire data file '{json_file_path_in_repo}' in commit {commit_hash[:7]}.")
            # Disappearance logic later will handle based on the final state of the batch.
            pass

        processed_fire_ids_in_this_commit = set()

        # 1. Process fires present in the current commit's JSON
        for fire_id, current_fire_data in current_commit_fires_map.items():
            processed_fire_ids_in_this_commit.add(fire_id)
            # This is the state of the fire *before this specific commit*
            # (either from DB load, or from a previous commit in this batch)
            previous_fire_data_for_comparison = in_memory_fire_states.get(fire_id)

            update_log_entry = {
                'fire_id': fire_id, 'commit_hash': commit_hash, 'commit_timestamp': commit_timestamp,
                'data_timestamp': current_fire_data.get('updated', {}).get('sec') or \
                                  current_fire_data.get('dateTime', {}).get('sec'),
                'status': current_fire_data.get('status'), 'status_code': current_fire_data.get('statusCode'),
                'man': current_fire_data.get('man'), 'terrain': current_fire_data.get('terrain'),
                'aerial': current_fire_data.get('aerial'), 'meios_aquaticos': current_fire_data.get('meios_aquaticos'),
                'active_in_commit': current_fire_data.get('active', False),
                'raw_data': json.dumps(current_fire_data)
            }

            cursor.execute("SELECT 1 FROM fires WHERE fire_id = ?", (fire_id,))
            fire_exists_in_db = cursor.fetchone()

            if not fire_exists_in_db: # Truly new fire to the system
                print(f"  NEW fire (to DB): {fire_id}")
                cursor.execute('''
                    INSERT INTO fires (fire_id, lat, lng, location, district, concelho, freguesia, natureza,
                                     first_seen_commit_hash, first_seen_data_timestamp,
                                     last_updated_commit_hash, last_updated_data_timestamp, is_currently_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (fire_id, current_fire_data.get('lat'), current_fire_data.get('lng'),
                      current_fire_data.get('location'), current_fire_data.get('district'),
                      current_fire_data.get('concelho'), current_fire_data.get('freguesia'),
                      current_fire_data.get('natureza'), commit_hash,
                      current_fire_data.get('dateTime', {}).get('sec'), commit_hash,
                      current_fire_data.get('updated', {}).get('sec') or current_fire_data.get('dateTime', {}).get('sec'),
                      current_fire_data.get('active', False)))
                update_log_entry['change_type'] = 'NEW'
            elif not previous_fire_data_for_comparison:
                # Exists in DB, but not in our `in_memory_fire_states` (e.g. disappeared then reappeared)
                # Or, more likely, it's the first time we see it in this *batch* of new commits.
                # We treat this as an update if its DB state was different.
                # The `compare_fire_data_are_different` needs a proper `previous_fire_data_for_comparison`.
                # This case implies it appeared *within this batch* after not being in `load_current_fire_states_from_db`.
                # This implies `fire_exists_in_db` should have been true, and `previous_fire_data_for_comparison`
                # should have been loaded by `load_current_fire_states_from_db`.
                # The only way `previous_fire_data_for_comparison` is None here, if `fire_exists_in_db` is True,
                # is if `load_current_fire_states_from_db` failed to load it (e.g., file missing in its last_updated_commit).
                # For safety, let's just treat it as if it's an update compared to a "null" previous state.
                print(f"  REAPPEARED or new in batch: {fire_id}")
                cursor.execute('''
                    UPDATE fires SET lat=?, lng=?, location=?, district=?, concelho=?, freguesia=?, natureza=?,
                                    last_updated_commit_hash=?, last_updated_data_timestamp=?, is_currently_active=?
                    WHERE fire_id=?
                ''', (current_fire_data.get('lat'), current_fire_data.get('lng'),
                      current_fire_data.get('location'), current_fire_data.get('district'),
                      current_fire_data.get('concelho'), current_fire_data.get('freguesia'),
                      current_fire_data.get('natureza'), commit_hash,
                      current_fire_data.get('updated', {}).get('sec') or current_fire_data.get('dateTime', {}).get('sec'),
                      current_fire_data.get('active', False), fire_id))
                update_log_entry['change_type'] = 'UPDATED' # Or 'REAPPEARED'
            else: # Fire exists in DB and we have its previous state for comparison
                if compare_fire_data_are_different(previous_fire_data_for_comparison, current_fire_data):
                    print(f"  UPDATED fire: {fire_id}")
                    cursor.execute('''
                        UPDATE fires SET lat=?, lng=?, location=?, district=?, concelho=?, freguesia=?, natureza=?,
                                        last_updated_commit_hash=?, last_updated_data_timestamp=?, is_currently_active=?
                        WHERE fire_id=?
                    ''', (current_fire_data.get('lat'), current_fire_data.get('lng'),
                          current_fire_data.get('location'), current_fire_data.get('district'),
                          current_fire_data.get('concelho'), current_fire_data.get('freguesia'),
                          current_fire_data.get('natureza'), commit_hash,
                          current_fire_data.get('updated', {}).get('sec') or current_fire_data.get('dateTime', {}).get('sec'),
                          current_fire_data.get('active', False), fire_id))
                    update_log_entry['change_type'] = 'UPDATED'
                else: # UNCHANGED but present in this commit
                    print(f"  UNCHANGED (still present) fire: {fire_id}")
                    cursor.execute('''UPDATE fires SET last_updated_commit_hash=? WHERE fire_id=?''', (commit_hash, fire_id))
                    # No fire_updates entry for "UNCHANGED" as per original logic.
                    update_log_entry = None # Signal not to log this

            if update_log_entry:
                cursor.execute('''
                    INSERT INTO fire_updates (fire_id, commit_hash, commit_timestamp, data_timestamp, status, status_code,
                                            man, terrain, aerial, meios_aquaticos, active_in_commit, change_type, raw_data)
                    VALUES (:fire_id, :commit_hash, :commit_timestamp, :data_timestamp, :status, :status_code,
                            :man, :terrain, :aerial, :meios_aquaticos, :active_in_commit, :change_type, :raw_data)
                ''', update_log_entry)

            # Update the in-memory state for this fire to reflect this commit's data
            in_memory_fire_states[fire_id] = current_fire_data
        
        # After processing all fires IN THIS COMMIT'S JSON:
        # Check for fires that were in our `in_memory_fire_states` (active or not) but are NOT in `current_commit_fires_map`.
        # These have "disappeared" *in this specific commit*.
        # The final `is_currently_active` status in `fires` table will be determined by the *last commit in the batch*.
        
        # Disappearance within the batch (fire gone from one commit to the next *within this batch*)
        fire_ids_in_memory_before_this_commit = set(in_memory_fire_states.keys())
        disappeared_in_this_commit_ids = fire_ids_in_memory_before_this_commit - processed_fire_ids_in_this_commit

        for fire_id in disappeared_in_this_commit_ids:
            last_data_for_fire = in_memory_fire_states[fire_id] # This is its state from the *previous* commit (or DB load)
            
            # If it was considered active before this commit, and now it's gone from the JSON
            if last_data_for_fire.get('active', False): # Check its 'active' status from *before* this commit
                print(f"  DISAPPEARED (in this commit): {fire_id}")
                # Update `fires` table. `is_currently_active` will be False.
                # `last_updated_commit_hash` points to *this* commit where it was observed missing.
                cursor.execute('''
                    UPDATE fires SET is_currently_active = ?, last_updated_commit_hash = ?
                    WHERE fire_id = ?
                ''', (False, commit_hash, fire_id))

                disappeared_log_entry = {
                    'fire_id': fire_id, 'commit_hash': commit_hash, 'commit_timestamp': commit_timestamp,
                    'data_timestamp': commit_timestamp, # Use commit time
                    'status': "Disappeared from source", 'status_code': None,
                    'man': last_data_for_fire.get('man'), 'terrain': last_data_for_fire.get('terrain'),
                    'aerial': last_data_for_fire.get('aerial'), 'meios_aquaticos': last_data_for_fire.get('meios_aquaticos'),
                    'active_in_commit': False, # Not in JSON, so not active in this commit
                    'change_type': 'DISAPPEARED',
                    'raw_data': json.dumps(last_data_for_fire) # Log its last known state
                }
                cursor.execute('''
                    INSERT INTO fire_updates (fire_id, commit_hash, commit_timestamp, data_timestamp, status, status_code,
                                            man, terrain, aerial, meios_aquaticos, active_in_commit, change_type, raw_data)
                    VALUES (:fire_id, :commit_hash, :commit_timestamp, :data_timestamp, :status, :status_code,
                            :man, :terrain, :aerial, :meios_aquaticos, :active_in_commit, :change_type, :raw_data)
                ''', disappeared_log_entry)
            
            # Update in-memory state to reflect it's not active in this commit's view
            if fire_id in in_memory_fire_states: # Should be true
                in_memory_fire_states[fire_id]['active'] = False # Mark it as inactive in our live state tracker
                # We don't remove it from in_memory_fire_states, as it might reappear in a later commit.

        newest_commit_processed_in_this_run = commit # Keep track of the latest commit SHA from this batch
        
        if (i + 1) % 20 == 0 or (i + 1) == len(commits_to_process): # Commit more frequently for smaller batches
            conn.commit()
            print(f"  -- Committed after processing commit {i+1}/{len(commits_to_process)} --")

    # After processing all new commits in the batch:
    if newest_commit_processed_in_this_run:
        update_last_processed_commit_hash(cursor, newest_commit_processed_in_this_run.hexsha)
        conn.commit()
        print(f"\nSuccessfully processed {len(commits_to_process)} commits.")
        print(f"Database updated. Last processed commit is now: {newest_commit_processed_in_this_run.hexsha[:7]}")
    else:
        # This case should ideally be caught earlier if commits_to_process was empty
        print("\nNo new commits were actually processed in this run.")
        if last_processed_hash and last_processed_hash == head_commit_hash:
             # This can happen if the script was run, found no new commits, and then this block is reached.
             print(f"Repository is already up-to-date with commit {head_commit_hash[:7]}.")
        # If last_processed_hash was None (first run) but repo was empty, commits_to_process is empty.
        elif not last_processed_hash and not list(repo.iter_commits()):
            print("Repository is empty. Nothing to process.")
        # update last_processed_hash to head if it was a full scan of an empty or already processed repo
        elif not last_processed_hash and head_commit_hash:
             update_last_processed_commit_hash(cursor, head_commit_hash)
             conn.commit()
             print(f"Initial scan complete. Repository HEAD is {head_commit_hash[:7]}.")


    conn.close()
    print(f"Processing complete. Database '{DB_NAME}' is updated.")

if __name__ == "__main__":
    # Ensure the target JSON file exists, at least in the latest commit, for a meaningful run.
    # Example: process_repository_incrementally("./path/to/your/git/repo", "data/fogos.json")
    process_repository_incrementally("../", "fogos.json")
    # To test a full rebuild scenario (e.g., after a schema change or messy history):
    # 1. Delete fires.sqlite (or just the 'last_processed_commit_hash' from script_metadata)
    # 2. Run the script. It will process all commits.