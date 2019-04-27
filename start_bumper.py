#!/usr/bin/env python3

import argparse
import logging
import bumper
import sys, socket
import time
import platform


def main():
    parser = argparse.ArgumentParser()

    if platform.system() == "Darwin":  # If a Mac, use 0.0.0.0 for listening
        listen_default = "0.0.0.0"
    else:
        listen_default = socket.gethostbyname(socket.gethostname())
        #listen_host = "localhost"  # Try this if the above doesn't work

    parser.add_argument('--listen', type=str, default=listen_default, help="listen address")
    parser.add_argument('--announce', type=str, default=None, help="announce address (for bot)")
    parser.add_argument('--debug', action="store_true")
    args = parser.parse_args()


    if args.debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format="[%(asctime)s] :: %(levelname)s :: %(name)s :: %(module)s :: %(funcName)s :: %(lineno)d :: %(message)s",
        )
    else:
        logging.basicConfig(
            level=logging.INFO,
            format="[%(asctime)s] :: %(levelname)s :: %(name)s :: %(message)s",
        )
        # format="[%(asctime)s] :: %(levelname)s :: %(name)s :: %(module)s :: %(funcName)s :: %(lineno)d :: %(message)s")


    conf_address_443 = (args.listen, 443)
    conf_address_8007 = (args.listen, 8007)
    xmpp_address = (args.listen, 5223)
    mqtt_address = (args.listen, 8883)
    announce_address = args.announce

    xmpp_server = bumper.XMPPServer(
        xmpp_address
    )
    mqtt_server = bumper.MQTTServer(mqtt_address)
    mqtt_helperbot = bumper.MQTTHelperBot(mqtt_address)
    conf_server = bumper.ConfServer(
        conf_address_443, announce=announce_address, usessl=True, helperbot=mqtt_helperbot
    )
    conf_server_2 = bumper.ConfServer(
        conf_address_8007, announce=announce_address, usessl=False, helperbot=mqtt_helperbot
    )

    # add user
    # users = bumper.bumper_users_var.get()
    # user1 = bumper.BumperUser('user1')
    # user1.add_device('devid')
    # user1.add_bot('bot_did')
    # users.append(user1)
    # bumper.bumper_users_var.set(users)

    # start xmpp server on port 5223 (sync)
    xmpp_server.run(run_async=True)  # Start in new thread

    # start mqtt server on port 8883 (async)
    mqtt_server.run(run_async=True)  # Start in new thread

    time.sleep(1.5)  # Wait for broker startup

    # start mqtt_helperbot (async)
    mqtt_helperbot.run(run_async=True)  # Start in new thread

    # start conf server on port 443 (async) - Used for most https calls
    conf_server.run(run_async=True)  # Start in new thread

    # start conf server on port 8007 (async) - Used for a load balancer request
    conf_server_2.run(run_async=True)  # Start in new thread

    while True:
        try:
            time.sleep(30)
            bumper.revoke_expired_tokens()
            disconnected_clients = bumper.get_disconnected_xmpp_clients()
            for client in disconnected_clients:
                xmpp_server.remove_client_byuid(client["userid"])

        except KeyboardInterrupt:
            bumper.bumperlog.info("Bumper Exiting - Keyboard Interrupt")
            print("Bumper Exiting")
            exit(0)


if __name__ == "__main__":
    main()
