import motor.motor_asyncio
from config import DB_URI, DB_NAME
from pytz import timezone
from datetime import datetime, timedelta

dbclient = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)
database = dbclient[DB_NAME]
activity_col = database['activity_logs']

DAYS = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']

async def log_activity(user_id: int):
    ist = timezone('Asia/Kolkata')
    now = datetime.now(ist)
    await activity_col.insert_one({
        'user_id': user_id,
        'hour': now.hour,
        'weekday': now.weekday(),
        'date': now.strftime('%Y-%m-%d'),
        'ts': now.timestamp()
    })

async def get_peak_hours_today():
    ist = timezone('Asia/Kolkata')
    today = datetime.now(ist).strftime('%Y-%m-%d')
    pipeline = [
        {'$match': {'date': today}},
        {'$group': {'_id': '$hour', 'count': {'$sum': 1}}},
        {'$sort': {'_id': 1}}
    ]
    results = await activity_col.aggregate(pipeline).to_list(length=None)
    hourly = {r['_id']: r['count'] for r in results}
    return hourly

async def get_peak_hours_week():
    ist = timezone('Asia/Kolkata')
    week_ago = (datetime.now(ist) - timedelta(days=7)).timestamp()
    pipeline = [
        {'$match': {'ts': {'$gte': week_ago}}},
        {'$group': {'_id': '$hour', 'count': {'$sum': 1}}},
        {'$sort': {'_id': 1}}
    ]
    results = await activity_col.aggregate(pipeline).to_list(length=None)
    hourly = {r['_id']: r['count'] for r in results}
    return hourly

async def get_daily_breakdown_week():
    ist = timezone('Asia/Kolkata')
    week_ago = (datetime.now(ist) - timedelta(days=7)).timestamp()
    pipeline = [
        {'$match': {'ts': {'$gte': week_ago}}},
        {'$group': {'_id': '$weekday', 'count': {'$sum': 1}}},
        {'$sort': {'_id': 1}}
    ]
    results = await activity_col.aggregate(pipeline).to_list(length=None)
    daily = {r['_id']: r['count'] for r in results}
    return daily

async def cleanup_old_logs(days: int = 30):
    ist = timezone('Asia/Kolkata')
    cutoff = (datetime.now(ist) - timedelta(days=days)).timestamp()
    result = await activity_col.delete_many({'ts': {'$lt': cutoff}})
    return result.deleted_count