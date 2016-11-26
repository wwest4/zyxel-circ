# What
Dumps Zyxel NAS metrics up to Circonus so you can alert on them (e.g. get an alert if a disk dies).

# Install

- Set up a circonus HTTPTrap check; note the URL + secret
- Run zyxel-circ.py as a cronjob (admin); ensure CIRCONUS_URL is set in the environment.

# Tested on
- Zyxel NSA320S


