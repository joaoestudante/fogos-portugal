# Single GET endpoint to return a JSON response with flask


from flask import Flask
from flask import jsonify
import sqlite3
from flask import request
from sqlalchemy import func
from flask_cors import CORS
import time

"""
D describe fires;
┌─────────────────────────────┬─────────────┬─────────┬─────────┬─────────┬─────────┐
│         column_name         │ column_type │  null   │   key   │ default │  extra  │
│           varchar           │   varchar   │ varchar │ varchar │ varchar │ varchar │
├─────────────────────────────┼─────────────┼─────────┼─────────┼─────────┼─────────┤
│ fire_id                     │ VARCHAR     │ YES     │ PRI     │ NULL    │ NULL    │
│ lat                         │ DOUBLE      │ YES     │ NULL    │ NULL    │ NULL    │
│ lng                         │ DOUBLE      │ YES     │ NULL    │ NULL    │ NULL    │
│ location                    │ VARCHAR     │ YES     │ NULL    │ NULL    │ NULL    │
│ district                    │ VARCHAR     │ YES     │ NULL    │ NULL    │ NULL    │
│ concelho                    │ VARCHAR     │ YES     │ NULL    │ NULL    │ NULL    │
│ freguesia                   │ VARCHAR     │ YES     │ NULL    │ NULL    │ NULL    │
│ natureza                    │ VARCHAR     │ YES     │ NULL    │ NULL    │ NULL    │
│ first_seen_commit_hash      │ VARCHAR     │ YES     │ NULL    │ NULL    │ NULL    │
│ first_seen_data_timestamp   │ BIGINT      │ YES     │ NULL    │ NULL    │ NULL    │
│ last_updated_commit_hash    │ VARCHAR     │ YES     │ NULL    │ NULL    │ NULL    │
│ last_updated_data_timestamp │ BIGINT      │ YES     │ NULL    │ NULL    │ NULL    │
│ is_currently_active         │ BIGINT      │ YES     │ NULL    │ NULL    │ NULL    │
├─────────────────────────────┴─────────────┴─────────┴─────────┴─────────┴─────────┤
│ 13 rows                                                                 6 columns │
└───────────────────────────────────────────────────────────────────────────────────┘
D describe fire_updates;
┌──────────────────┬─────────────┬─────────┬─────────┬─────────┬─────────┐
│   column_name    │ column_type │  null   │   key   │ default │  extra  │
│     varchar      │   varchar   │ varchar │ varchar │ varchar │ varchar │
├──────────────────┼─────────────┼─────────┼─────────┼─────────┼─────────┤
│ update_id        │ BIGINT      │ YES     │ PRI     │ NULL    │ NULL    │
│ fire_id          │ VARCHAR     │ YES     │ NULL    │ NULL    │ NULL    │
│ commit_hash      │ VARCHAR     │ YES     │ NULL    │ NULL    │ NULL    │
│ commit_timestamp │ BIGINT      │ YES     │ NULL    │ NULL    │ NULL    │
│ data_timestamp   │ BIGINT      │ YES     │ NULL    │ NULL    │ NULL    │
│ status           │ VARCHAR     │ YES     │ NULL    │ NULL    │ NULL    │
│ status_code      │ BIGINT      │ YES     │ NULL    │ NULL    │ NULL    │
│ man              │ BIGINT      │ YES     │ NULL    │ NULL    │ NULL    │
│ terrain          │ BIGINT      │ YES     │ NULL    │ NULL    │ NULL    │
│ aerial           │ BIGINT      │ YES     │ NULL    │ NULL    │ NULL    │
│ meios_aquaticos  │ BIGINT      │ YES     │ NULL    │ NULL    │ NULL    │
│ active_in_commit │ BIGINT      │ YES     │ NULL    │ NULL    │ NULL    │
│ change_type      │ VARCHAR     │ YES     │ NULL    │ NULL    │ NULL    │
│ raw_data         │ VARCHAR     │ YES     │ NULL    │ NULL    │ NULL    │
├──────────────────┴─────────────┴─────────┴─────────┴─────────┴─────────┤
│ 14 rows                                                      6 columns │
└────────────────────────────────────────────────────────────────────────┘
"""

# SQL Alchemy models for the tables above

from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class Fire(Base):
    __tablename__ = 'fires'
    fire_id = Column(String, primary_key=True)
    lat = Column(Float)
    lng = Column(Float)
    location = Column(String)
    district = Column(String)
    concelho = Column(String)
    freguesia = Column(String)
    natureza = Column(String)
    first_seen_commit_hash = Column(String)
    first_seen_data_timestamp = Column(Integer)
    last_updated_commit_hash = Column(String)
    last_updated_data_timestamp = Column(Integer)
    is_currently_active = Column(Integer)

    def to_dict(self):
        return {
            'fire_id': self.fire_id,
            'lat': self.lat,
            'lng': self.lng,
            'location': self.location,
            'district': self.district,
            'concelho': self.concelho,
            'freguesia': self.freguesia,
            'natureza': self.natureza,
            'first_seen_commit_hash': self.first_seen_commit_hash,
            'first_seen_data_timestamp': self.first_seen_data_timestamp,
            'last_updated_commit_hash': self.last_updated_commit_hash,
            'last_updated_data_timestamp': self.last_updated_data_timestamp,
            'is_currently_active': self.is_currently_active
        }

class FireUpdate(Base):
    __tablename__ = 'fire_updates'
    update_id = Column(Integer, primary_key=True)
    fire_id = Column(String)
    commit_hash = Column(String)
    commit_timestamp = Column(Integer)
    data_timestamp = Column(Integer)
    status = Column(String)
    status_code = Column(Integer)
    man = Column(Integer)
    terrain = Column(Integer)
    aerial = Column(Integer)
    meios_aquaticos = Column(Integer)

    def to_dict(self):
        return {
            'update_id': self.update_id,
            'fire_id': self.fire_id,
            'commit_hash': self.commit_hash,
            'commit_timestamp': self.commit_timestamp,
            'data_timestamp': self.data_timestamp,
            'status': self.status,
            'status_code': self.status_code
        }


app = Flask(__name__)
CORS(app)

def getDBSession():
    # Connect to the SQLite database with SQL Alchemy
    engine = create_engine('sqlite:///fires.sqlite')
    Session = sessionmaker(bind=engine)
    return Session()

# Route to get all fires, paginated
@app.route('/fires', methods=['GET'])
def get_fires():
    page = int(request.args.get('page', 0))
    page_size = int(request.args.get('page_size', 25))
    search_term = request.args.get('search_term', None)    
    session = getDBSession()
    # Get the data from the database
    fires = []
    if (search_term is None):
        fires = session.query(Fire).offset(page * page_size).limit(page_size).all()
    else:
        print(search_term)
        fires = session.query(Fire).filter(Fire.location.like("%" + search_term + "%")).offset(page * page_size).limit(page_size).all()
    # Convert the data to a list of dictionaries
    fires_list = [fire.to_dict() for fire in fires]
    session.close()
    # Return the data as a JSON response
    return jsonify(fires_list)

def get_query_with_date_filters(query):
    # Apply date filters if provided
    from_date = request.args.get('fromDate', type=int) / 1000
    to_date = request.args.get('toDate', type=int) / 1000
    new_query = query
    if from_date is not None:
        new_query = new_query.filter(Fire.first_seen_data_timestamp >= from_date)
    if to_date is not None:
        new_query = new_query.filter(Fire.first_seen_data_timestamp <= to_date)
    return new_query


# Route to get number of fires grouped per month, for all time
@app.route('/fires/months', methods=['GET'])
def get_fires_per_month():
    session = getDBSession()

    query = session.query(
        func.strftime('%Y-%m', func.datetime(Fire.first_seen_data_timestamp, 'unixepoch')).label('month'),
        func.count().label('count')
    )

    query = get_query_with_date_filters(query)

    results = query.group_by('month').order_by('month').all()
    session.close()
    # Convert the data to a list of dictionaries
    results = [{'month': month, 'count': count} for month, count in results]
    return jsonify(list(results))

@app.route('/fires/total', methods=['GET'])
def get_fires_total():
    session = getDBSession()
    
    query = session.query(func.count(Fire.fire_id))
    query = get_query_with_date_filters(query)
    total = query.scalar()

    session.close()
    return jsonify({'value': total})    

@app.route('/fires/most-affected-district', methods=['GET'])
def get_most_affected_district():
    session = getDBSession()
    query = session.query(
        Fire.district,
        func.count(Fire.fire_id).label('count')
    ).group_by(Fire.district).order_by(func.count(Fire.fire_id).desc())

    query = get_query_with_date_filters(query)
    result = query.first()
    session.close()
    if result:
        return jsonify({'value': result[0], 'subValue': result[1]})
    else:
        return jsonify({'value': 'None'})
    
@app.route('/fires/count-per-district', methods=['GET'])
def get_fires_count_per_district():
    session = getDBSession()
    results = get_query_with_date_filters(session.query(
        Fire.district,
        func.count(Fire.fire_id).label('count')
    ).group_by(Fire.district).order_by(func.count(Fire.fire_id).desc())).all()
    session.close()
    # Convert the data to a list of dictionaries
    results = [{'district': district, 'count': count} for district, count in results]
    return jsonify(list(results))

import numpy as np

@app.route('/fires/duration-histogram', methods=['GET'])
def get_fires_duration_histogram():
    session = getDBSession()
    
    # Query to calculate the duration of each fire
    durations = session.query((Fire.last_updated_data_timestamp - Fire.first_seen_data_timestamp).label('duration')).all()
    session.close()
    
    # Extract durations into a list
    duration_values = [d[0] / 3600 for d in durations if d[0] is not None]
    # Define bins with a size of 0.5 for the first 30 bins
    bin_edges = [i * 0.5 for i in range(25)]  # 0, 0.5, 1.0, ..., 15.0
    # Add the last bin edge for the last bin, with the max value
    max_value = max(duration_values) if duration_values else 0
    bin_edges.append(max_value)
    
    # Compute the histogram
    histogram, bin_edges = np.histogram(duration_values, bins=bin_edges)
    # Format the histogram as a list of dictionaries
    histogram_data = [
        {'label': str(round(float(bin_edges[i]), 1)) + '-' + str(round(float(bin_edges[i + 1]),1)), 'count': int(histogram[i])}
        for i in range(len(histogram))
    ]
    histogram_data[-1]["label"] = '> ' + str(round(float(bin_edges[-2]), 1))
    
    # Return the histogram as JSON
    return jsonify(histogram_data)

@app.route('/fires/duration-stats', methods=['GET'])
def get_fires_average_duration():
    session = getDBSession()
    # Calculate the average, median, and standard deviation of the duration
    durations = session.query((Fire.last_updated_data_timestamp - Fire.first_seen_data_timestamp).label('duration')).all()
    session.close()
    # Extract durations into a list
    duration_values = [d[0] / 3600 for d in durations if d[0] is not None]
    if len(duration_values) == 0:
        return jsonify({'average': 0, 'median': 0, 'std_dev': 0})
    average = np.mean(duration_values)
    median = np.median(duration_values)
    value = f"Median: {median:.2f}"
    return jsonify({'value': round(average, 2), 'subValue': value})
    

@app.route('/fires/worst-day-stats', methods=['GET'])
def get_worst_day_stats():
    session = getDBSession()
    
    # Step 1: Get the day with the most fires
    worst_day_result = get_query_with_date_filters(session.query(
        func.strftime('%Y-%m-%d', func.datetime(Fire.first_seen_data_timestamp, 'unixepoch')).label('day'),
        func.count(Fire.fire_id).label('count')
    ).group_by('day').order_by(func.count(Fire.fire_id).desc())).first()
    
    if not worst_day_result:
        session.close()
        return jsonify({'message': 'No data available for worst day stats.'})
    
    worst_day = worst_day_result.day
    
    # Step 2: Get total resources deployed on the worst day
    total_resources_result = session.query(
        func.sum(func.coalesce(FireUpdate.man, 0)).label('total_man'),
        func.sum(func.coalesce(FireUpdate.terrain, 0)).label('total_terrain'),
        func.sum(func.coalesce(FireUpdate.aerial, 0)).label('total_aerial')
    ).join(Fire, Fire.fire_id == FireUpdate.fire_id).filter(
        func.strftime('%Y-%m-%d', func.datetime(Fire.first_seen_data_timestamp, 'unixepoch')) == worst_day
    ).first()
    
    total_man = total_resources_result.total_man or 0
    total_terrain = total_resources_result.total_terrain or 0
    total_aerial = total_resources_result.total_aerial or 0
    
    # Step 3: Get the largest duration of a fire and its ID on the worst day
    largest_duration_result = session.query(
        Fire.fire_id,
        func.max(Fire.last_updated_data_timestamp - Fire.first_seen_data_timestamp).label('max_duration')
    ).filter(
        func.strftime('%Y-%m-%d', func.datetime(Fire.first_seen_data_timestamp, 'unixepoch')) == worst_day
    ).first()
    
    largest_duration = (largest_duration_result.max_duration or 0) / 3600  # Convert to hours
    fire_with_longest_duration = largest_duration_result.fire_id if largest_duration_result else None
    
    # Step 4: Get the districts that had fires on the worst day
    districts_result = session.query(
        Fire.district
    ).filter(
        func.strftime('%Y-%m-%d', func.datetime(Fire.first_seen_data_timestamp, 'unixepoch')) == worst_day
    ).distinct().all()
    
    districts = [district[0] for district in districts_result]
    
    session.close()
    
    # Return the stats as JSON
    return jsonify({
        'worst_day': worst_day,
        'total_fires': worst_day_result.count,
        'total_resources': {
            'man': total_man,
            'terrain': total_terrain,
            'aerial': total_aerial
        },
        'largest_fire_duration_hours': f"{round(divmod(largest_duration,1)[0])}h{round(divmod(largest_duration,1)[1] * 60)}m",
        'fire_with_longest_duration': fire_with_longest_duration,
        'districts': districts
    })

@app.route('/fires/available-date-range', methods=['GET'])
def get_available_date_range():
    session = getDBSession()
    
    # Get the minimum and maximum dates from the first_seen_data_timestamp
    min_date_result = session.query(func.min(Fire.first_seen_data_timestamp)).scalar()
    max_date_result = session.query(func.max(Fire.first_seen_data_timestamp)).scalar()
    
    session.close()
    
    if min_date_result and max_date_result:
        return jsonify({
            'min_date': min_date_result,
            'max_date': max_date_result
        })
    else:
        return jsonify({'message': 'No data available for date range.'})
    
if __name__ == '__main__':
    app.run(debug=True)