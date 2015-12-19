#!/usr/bin/env bash

set -e

read -p "Is your virtualenv activated? If not, please activate it first. [y/N] " START

if [ "$START" != "y" ]; then
    exit
fi

read -p "Do you want to install Python requirements? [y/N] " PYTHON
read -p "Do you want to install Ruby requirements? [y/N] " RUBY

if [ "$PYTHON" = "y" ]; then
    pip install -r requirements/debug.txt
fi

if [ "$RUBY" = "y" ]; then
    [ -e "$HOME/.rvm/scripts/rvm" ] && source "$HOME/.rvm/scripts/rvm"
    rvm install $(grep "ruby '" Gemfile | sed "s/ruby '\(.*\)'/\1/")
    rvm gemset create score-phorum
    rvm gemset use score-phorum
    gem install bundler
    bundle install
fi
