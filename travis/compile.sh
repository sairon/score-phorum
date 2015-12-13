#!/usr/bin/env bash

set -e

# compile Sass into CSS
(
    cd phorum/static
    compass compile
)

# clean and create deployment directory
rm -rf deployment
mkdir deployment

# copy files to deployment directory
rsync -avR . deployment/ \
    --exclude /deployment \
    --exclude /.git \
    --exclude /.gitignore \
    --exclude /.travis.yml \
    --exclude /dev \
    --exclude /travis \
    --exclude /static \
    --exclude /vagrant \
    --exclude /Vagrantfile \
    --exclude /phorum/static/.sass-cache \
    --exclude /phorum/static/sass

# create .gitignore for deployment
cat > deployment/.gitignore <<GITIGNORE
*.py[cod]
/media/*
/static/*
local_settings.json
GITIGNORE

if [[ -z ${TRAVIS_BRANCH} ]]; then DEPLOY_BRANCH=$(git rev-parse --abbrev-ref HEAD)
else DEPLOY_BRANCH=${TRAVIS_BRANCH}; fi
DEPLOY_HASH=$(git log -n1 --pretty="%H")

(
    cd deployment
    git init
    git config user.name "Travis-CI"
    git config user.email "travis@scorephorum.cz"
    git add .
    git commit -m "Deployment of https://github.com/sairon/score-phorum/commit/${DEPLOY_HASH}"
    git push -f -q "https://${GH_TOKEN}@${GH_REF}" master:deploy-${DEPLOY_BRANCH} > /dev/null 2>&1 || exit 1
) || echo "Pushing to the GH repository failed" >&2
