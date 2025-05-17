## What is this?
This repository contains the change history of fire data in Portugal from fogos.pt. Idea taken from: https://simonwillison.net/2020/Oct/9/git-scraping/

## How does it work?

Every 5 minutes, a Github action is executed and fetches https://api-dev.fogos.pt/new/fires. This URL is used by the fogos.pt website to show the relevant fires in Portugal.

By saving the response with Git, we can analyze over time the evoution of each fire, and the fires in general. Although Simon made a purpose built tool for this analysis (https://simonwillison.net/2021/Dec/7/git-history/) I opted to ask Gemini 2.5 Pro to build something more relevant for this use case. The script reads the git history and builds an sqlite3 database that is then interacted with via Flask and a React frontend.
