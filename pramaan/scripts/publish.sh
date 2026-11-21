#!/usr/bin/env bash
# Publish Pramaan as its own repository, with its full history.
#
# 1. Create the empty repo (one click, fields prefilled):
#    https://github.com/new?name=pramaan&visibility=public&description=Catch+fake+case+citations+in+Indian+legal+documents.+Free%2C+open-source%2C+private.
#    Leave "Add a README" and "Add license" unticked.
# 2. On your laptop, from a clone of your profile repo:
#    git fetch origin claude/wonderful-euler-sq9rg0 && git checkout claude/wonderful-euler-sq9rg0
#    bash pramaan/scripts/publish.sh
# 3. In the new repo: Settings -> Pages -> Source: GitHub Actions. The site appears at
#    https://vividhdesign.github.io/pramaan/ a few minutes later.
set -euo pipefail

OWNER="${OWNER:-VividhDesign}"
REPO="${REPO:-pramaan}"
TAG="${TAG:-v0.1.0}"
ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if ! git ls-remote "https://github.com/$OWNER/$REPO.git" >/dev/null 2>&1; then
  echo "Repository $OWNER/$REPO not found. Create it first:"
  echo "  https://github.com/new?name=$REPO&visibility=public"
  exit 1
fi

echo "Splitting pramaan/ into its own history..."
git branch -D pramaan-standalone >/dev/null 2>&1 || true
git subtree split --prefix pramaan -b pramaan-standalone

echo "Pushing to github.com/$OWNER/$REPO (main)..."
git push "https://github.com/$OWNER/$REPO.git" pramaan-standalone:main

if [ "${NO_TAG:-}" != "1" ]; then
  echo "Tagging $TAG (publishes to PyPI once trusted publishing is set up; see docs/LAUNCH.md)..."
  git tag -f "$TAG" pramaan-standalone
  git push "https://github.com/$OWNER/$REPO.git" "refs/tags/$TAG" || \
    echo "Tag push failed; push it later with: git push https://github.com/$OWNER/$REPO.git $TAG"
fi

cat <<EOF

Done. Remaining clicks:
  * https://github.com/$OWNER/$REPO/settings/pages  -> Source: GitHub Actions
  * https://github.com/$OWNER/$REPO  -> About (gear): add website https://vividhdesign.github.io/$REPO/
    and topics: legal-tech india hallucination citations supreme-court nlp
  * Merge branch claude/wonderful-euler-sq9rg0 into main of your profile repo (adds Pramaan to your profile).
EOF
