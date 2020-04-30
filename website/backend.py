import json
from datetime import datetime as dt
from urllib.parse import unquote

import aiohttp
import aiohttp_session
from aiohttp.web import HTTPFound, Request, RouteTableDef, Response

from website import utils as webutils

routes = RouteTableDef()


@routes.get('/login_redirect')
async def login(request:Request):
    """Page the discord login redirects the user to when successfully logged in with Discord"""

    await webutils.process_discord_login(request, ['identify', 'guilds'])
    session = await aiohttp_session.get_session(request)
    return HTTPFound(location=session.pop('redirect_on_login', '/'))


@routes.post('/webhooks/paypal/purchase_ipn')
async def paypal_purchase_complete(request:Request):
    """Handles Paypal throwing data my way"""

    # Get the data
    content_bytes: bytes = await request.content.read()
    paypal_data_string: str = content_bytes.decode()

    # Send the data back to see if it's valid
    data_send_back = "cmd=_notify-validate&" + paypal_data_string
    async with aiohttp.ClientSession(loop=request.app.loop) as session:
        paypal_url = {
            True: "https://ipnpb.sandbox.paypal.com/cgi-bin/webscr",
            False: "https://ipnpb.paypal.com/cgi-bin/webscr",
        }.get(request.app['config']['paypal_pdt']['sandbox'])
        async with session.post(paypal_url, data=data_send_back) as site:
            site_data = await site.read()
            if site_data.decode() != "VERIFIED":
                return Response(status=200)  # Oh no it was fake data

    # Get the data from PP
    paypal_data = {unquote(i.split('=')[0].replace("+", " ")):unquote(i.split('=')[1].replace("+", " ")) for i in paypal_data_string.split('&')}
    try:
        custom_data = json.loads(paypal_data['custom'])
    except Exception:
        custom_data = {}
    payment_amount = int(paypal_data.get('mc_gross', '0').replace('.', ''))

    # See if we want to handle it at all
    if paypal_data['txn_type'] not in ['web_accept', 'express_checkout']:
        return Response(status=200)  # Not the right thing

    # Make sure it's to the right person
    if paypal_data['receiver_email'] != request.app['config']['paypal_pdt']['receiver_email']:
        return Response(status=200)  # Wrong email passed

    # See if it's refunded data
    refunded = False
    if payment_amount < 0:
        if paypal_data['payment_status'] == 'Refunded' or paypal_data['payment_status'] == 'Reversed':
            refunded = True
        else:
            return Response(status=200)

    # Database the relevant data
    db_data = {
        'completed': paypal_data['payment_status'] == 'Completed',
        'checkout_complete_timestamp': dt.utcnow(),
        'customer_id': paypal_data['payer_id'],
        'id': paypal_data['txn_id'],
        'payment_amount': payment_amount,
        'discord_id': int(custom_data['discord_user_id']),
        'guild_id': 0,
    }
    if db_data['completed'] is False:
        db_data['checkout_complete_timestamp'] = None
    async with request.app['database']() as db:
        await db(
            """INSERT INTO paypal_purchases
            (id, customer_id, payment_amount, discord_id, guild_id, completed, checkout_complete_timestamp) VALUES
            ($1, $2, $3, $4, $5, $6, $7) ON CONFLICT (id) DO UPDATE SET completed=$6, checkout_complete_timestamp=$7,
            guild_id=$5, discord_id=$4, customer_id=$2""",
            db_data['id'], db_data['customer_id'], db_data['payment_amount'], db_data['discord_id'],
            db_data['guild_id'], db_data['completed'], db_data['checkout_complete_timestamp'],
        )

    # Put your additional processing here

    # Let the user get redirected
    return Response(status=200)
