#!/bin/sh

# this env variable is configured crons/envs
# -> it controls how frequently the mgmt commands are run
echo "$POLL_FREQ_CRON_MINUTE * * * * /app/crons/run.sh > /dev/pts/0" > /etc/crontabs/root

echo ""
echo ""
echo "##########"
cat /etc/crontabs/root
echo "##########"
echo ""
echo ""

# start cron daemon
crond

