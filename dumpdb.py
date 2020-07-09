all_users = [i.to_json() for i in utils.FamilyTreeMember.get(author.id).span(expand_upwards=True, add_parent=True)]
data = []
added_users = set()

for user in all_users:
    if user['discord_id'] not in added_users:
        added_users.add(user['discord_id'])
        data.append("MERGE (U{0}:User {{user_id: {0}}})".format(user['discord_id']))
    if user['partner_id'] and user['partner_id'] not in added_users:
        added_users.add(user['partner_id'])
        data.append("MERGE (U{0}:User {{user_id: {0}}})".format(user['partner_id']))
    if user['parent_id'] and user['parent_id'] not in added_users:
        added_users.add(user['parent_id'])
        data.append("MERGE (U{0}:User {{user_id: {0}}})".format(user['parent_id']))

    if user['partner_id']:
        data.append("MERGE (U{0})-[:MARRIED_TO]->(U{1})".format(user['discord_id'], user['partner_id']))
    if user['parent_id']:
        data.append("MERGE (U{0})-[:CHILD_OF]->(U{1})".format(user['discord_id'], user['parent_id']))
        data.append("MERGE (U{1})-[:PARENT_OF]->(U{0})".format(user['discord_id'], user['parent_id']))

return ' '.join(data)
