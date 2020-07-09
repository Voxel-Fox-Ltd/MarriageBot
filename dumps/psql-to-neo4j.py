import asyncio
import logging
from datetime import datetime as dt
import random
import string

from aioneo4j import Neo4j
import asyncpg


logging.basicConfig()
logging.getLogger("aioneo4j").setLevel(logging.CRITICAL)


def get_identifier():
    return ''.join(random.choices(string.ascii_letters, k=10))


async def main():
    # Read db
    connection = await asyncpg.connect(user='marriagebot', password='discordio', database='marriagebot', port=5432, host='127.0.0.1')
    marriages = await connection.fetch("SELECT * FROM marriages")
    children = await connection.fetch("SELECT * FROM parents")
    await connection.close()

    # Shove them into Neo4j
    async with Neo4j(host='127.0.0.1', port=7474, user='neo4j', password='compression', database='marriagebottest') as client:

        merges = []

        for counter, row in enumerate(marriages, start=1, offset=8300):
            user_identifier = get_identifier()
            partner_identifier = get_identifier()
            merges.append(f"MERGE ({user_identifier}:FamilyTreeMember {{user_id: {row['user_id']}}})")
            merges.append(f"MERGE ({partner_identifier}:FamilyTreeMember {{user_id: {row['partner_id']}}})")
            if row['timestamp']:
                merges.append(f"MERGE ({user_identifier})-[:MARRIED_TO {{timestamp: {row['timestamp'].timestamp()}, guild_id: {row['guild_id']}}}]->({partner_identifier})-[:MARRIED_TO {{timestamp: {row['timestamp'].timestamp()}, guild_id: {row['guild_id']}}}]->({user_identifier})")
            else:
                merges.append(f"MERGE ({user_identifier})-[:MARRIED_TO {{guild_id: {row['guild_id']}}}]->({partner_identifier})-[:MARRIED_TO {{guild_id: {row['guild_id']}}}]->({user_identifier})")

            if counter % 50 == 0:
                print(f"Running {' '.join(merges)};")
                await client.cypher(' '.join(merges) + ';')
                merges.clear()

        for counter, row in enumerate(children, start=1):
            parent_identifier = get_identifier()
            child_identifier = get_identifier()
            merges.append(f"MERGE ({parent_identifier}:FamilyTreeMember {{user_id: {row['parent_id']}}})")
            merges.append(f"MERGE ({child_identifier}:FamilyTreeMember {{user_id: {row['child_id']}}})")
            if row['timestamp']:
                merges.append(f"MERGE ({parent_identifier})-[:PARENT_OF {{timestamp: {row['timestamp'].timestamp()}, guild_id: {row['guild_id']}}}]->({child_identifier})-[:CHILD_OF {{timestamp: {row['timestamp'].timestamp()}, guild_id: {row['guild_id']}}}]->({parent_identifier})")
            else:
                merges.append(f"MERGE ({parent_identifier})-[:PARENT_OF {{guild_id: {row['guild_id']}}}]->({child_identifier})-[:CHILD_OF {{guild_id: {row['guild_id']}}}]->({parent_identifier})")

            if counter % 50 == 0:
                print(f"Running {' '.join(merges)};")
                await client.cypher(' '.join(merges) + ';')
                merges.clear()

        if merges:
            print(f"Running {' '.join(merges)};")
            await client.cypher(' '.join(merges) + ';')
            merges.clear()


async def getdata():

    # Shove them into Neo4j
    async with Neo4j(host='127.0.0.1', port=7474, user='neo4j', password='compression', database='marriagebottest') as client:
        _, data = await client.cypher('MATCH (n:User {{user_id: 562131796603568158}})')

print(dt.utcnow())
try:
    asyncio.get_event_loop().run_until_complete(main())
except Exception as e:
    print(dt.utcnow())
    raise e
print(dt.utcnow())
