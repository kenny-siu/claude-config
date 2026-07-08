#!/usr/bin/env python3
"""Thin CLI over the Linear GraphQL API (https://api.linear.app/graphql).

Auth comes from the LINEAR_API_KEY environment variable.
Run with no arguments (or --help) to see the command list.
Output is plain text designed to be read by a model, not parsed.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

API_URL = "https://api.linear.app/graphql"

# Workspace defaults, used by `create` when flags are omitted.
DEFAULT_TEAM_KEY = os.environ.get("LINEAR_DEFAULT_TEAM", "")
DEFAULT_STATE = "Ready for Development"
DEFAULT_PRIORITY = 4  # Low

# Comment bodies that are pure Slack-sync plumbing, safe to drop entirely.
SYNC_BOILERPLATE_MARKERS = (
    "This comment thread is synced to a corresponding",
    "Created issue [",
)


def die(message):
    print(f"error: {message}", file=sys.stderr)
    sys.exit(1)


def gql(query, variables=None):
    api_key = os.environ.get("LINEAR_API_KEY")
    if not api_key:
        die("LINEAR_API_KEY is not set. Export it or add it to your shell profile.")
    payload = json.dumps({"query": query, "variables": variables or {}}).encode()
    request = urllib.request.Request(
        API_URL,
        data=payload,
        headers={"Authorization": api_key, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = json.load(response)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:2000]
        die(f"HTTP {exc.code} from Linear: {detail}")
    except urllib.error.URLError as exc:
        die(f"could not reach Linear: {exc.reason}")
    if body.get("errors"):
        messages = "; ".join(e.get("message", str(e)) for e in body["errors"])
        die(f"GraphQL error: {messages}")
    return body["data"]


def viewer_id():
    return gql("{ viewer { id } }")["viewer"]["id"]


def fetch_team(team_key):
    data = gql(
        """query($key: String!) {
             teams(filter: { key: { eq: $key } }) {
               nodes {
                 id key name
                 states { nodes { id name type } }
                 activeCycle { id number endsAt }
               }
             }
           }""",
        {"key": team_key},
    )
    nodes = data["teams"]["nodes"]
    if not nodes:
        die(f"no team with key '{team_key}'. Run `teams` to list them.")
    return nodes[0]


def resolve_state_id(team, state_name):
    for state in team["states"]["nodes"]:
        if state["name"].lower() == state_name.lower():
            return state["id"]
    names = ", ".join(s["name"] for s in team["states"]["nodes"])
    die(f"team {team['key']} has no state '{state_name}'. States: {names}")


def print_issue_line(issue):
    state = issue.get("state") or {}
    assignee = issue.get("assignee") or {}
    parts = [issue["identifier"], f"[{state.get('name', '?')}]", issue["title"]]
    if assignee:
        parts.append(f"(assignee: {assignee['name']})")
    print("  ".join(parts))


ISSUE_FIELDS = """
  id identifier title description url branchName
  priority priorityLabel estimate
  createdAt updatedAt
  state { name type }
  assignee { name }
  creator { name }
  team { key name }
  cycle { number }
  project { name }
  parent { identifier title }
  labels { nodes { name } }
  children { nodes { identifier title state { name } } }
  relations { nodes { type relatedIssue { identifier title } } }
  inverseRelations { nodes { type issue { identifier title } } }
  attachments { nodes { title url sourceType } }
"""


def cmd_whoami(_args):
    data = gql("{ viewer { id name email } organization { name urlKey } }")
    v, org = data["viewer"], data["organization"]
    print(f"{v['name']} <{v['email']}>  id={v['id']}  org={org['name']} ({org['urlKey']})")


def cmd_issue(args):
    data = gql(
        "query($id: String!) { issue(id: $id) { %s } }" % ISSUE_FIELDS,
        {"id": args.id},
    )
    issue = data["issue"]
    state = issue["state"]
    print(f"{issue['identifier']}: {issue['title']}")
    print(f"state: {state['name']}  priority: {issue['priorityLabel']}  estimate: {issue['estimate']}")
    assignee = issue["assignee"]
    creator = issue["creator"]
    print(f"assignee: {assignee['name'] if assignee else 'none'}  creator: {creator['name'] if creator else 'unknown'}")
    print(f"team: {issue['team']['key']} ({issue['team']['name']})", end="")
    if issue["cycle"]:
        print(f"  cycle: {issue['cycle']['number']}", end="")
    if issue["project"]:
        print(f"  project: {issue['project']['name']}", end="")
    print()
    labels = [l["name"] for l in issue["labels"]["nodes"]]
    if labels:
        print(f"labels: {', '.join(labels)}")
    print(f"url: {issue['url']}")
    print(f"branch: {issue['branchName']}")
    if issue["parent"]:
        print(f"parent: {issue['parent']['identifier']} {issue['parent']['title']}")
    for child in issue["children"]["nodes"]:
        print(f"child: {child['identifier']} [{child['state']['name']}] {child['title']}")
    for rel in issue["relations"]["nodes"]:
        other = rel["relatedIssue"]
        print(f"relation ({rel['type']}): {other['identifier']} {other['title']}")
    for rel in issue["inverseRelations"]["nodes"]:
        other = rel["issue"]
        print(f"relation ({rel['type']}, inverse): {other['identifier']} {other['title']}")
    for att in issue["attachments"]["nodes"]:
        print(f"attachment [{att['sourceType'] or 'link'}]: {att['title']} — {att['url']}")
    print()
    print("--- description ---")
    print(issue["description"] or "(empty)")
    print()
    print_comments(args.id)


def print_comments(issue_id):
    data = gql(
        """query($id: String!) {
             issue(id: $id) {
               comments(first: 100) {
                 nodes {
                   id body createdAt
                   user { name }
                   botActor { name }
                   parent { id }
                 }
               }
             }
           }""",
        {"id": issue_id},
    )
    comments = data["issue"]["comments"]["nodes"]
    kept = [
        c for c in comments
        if not any(marker in c["body"] for marker in SYNC_BOILERPLATE_MARKERS)
    ]
    dropped = len(comments) - len(kept)
    kept.sort(key=lambda c: c["createdAt"])
    print(f"--- comments ({len(kept)} shown, {dropped} sync-bot posts hidden) ---")
    if not kept:
        print("(none)")
    for c in kept:
        author = (c["user"] or {}).get("name") or (c["botActor"] or {}).get("name") or "unknown"
        bot_tag = " [bot]" if c["botActor"] else ""
        reply_tag = "  ↳ " if c["parent"] else ""
        print(f"\n{reply_tag}{author}{bot_tag} ({c['createdAt'][:10]}):")
        body = c["body"].strip()
        indent = "    " if c["parent"] else ""
        for line in body.splitlines():
            print(f"{indent}{line}")


def cmd_comments(args):
    print_comments(args.id)


def cmd_search(args):
    team_filter = ""
    variables = {"term": args.term, "limit": args.limit}
    if args.team:
        team_filter = ", filter: { team: { key: { eq: $team } } }"
        variables["team"] = args.team
    query = (
        "query($term: String!, $limit: Int!%s) {"
        "  searchIssues(term: $term, first: $limit%s) {"
        "    nodes { identifier title state { name } assignee { name } team { key } }"
        "  }"
        "}" % (", $team: String!" if args.team else "", team_filter)
    )
    nodes = gql(query, variables)["searchIssues"]["nodes"]
    if not nodes:
        print("no matches")
    for issue in nodes:
        print_issue_line(issue)


def cmd_list(args):
    filters = []
    variables = {"limit": args.limit}
    declarations = ["$limit: Int!"]
    if args.team:
        filters.append("team: { key: { eq: $team } }")
        declarations.append("$team: String!")
        variables["team"] = args.team
    if args.assignee:
        if args.assignee == "me":
            filters.append("assignee: { id: { eq: $assigneeId } }")
            declarations.append("$assigneeId: ID!")
            variables["assigneeId"] = viewer_id()
        else:
            filters.append("assignee: { name: { containsIgnoreCase: $assigneeName } }")
            declarations.append("$assigneeName: String!")
            variables["assigneeName"] = args.assignee
    if args.state:
        filters.append("state: { name: { eqIgnoreCase: $stateName } }")
        declarations.append("$stateName: String!")
        variables["stateName"] = args.state
    filter_clause = f", filter: {{ {', '.join(filters)} }}" if filters else ""
    query = (
        "query(%s) { issues(first: $limit, orderBy: updatedAt%s) {"
        "  nodes { identifier title state { name } assignee { name } updatedAt }"
        "} }" % (", ".join(declarations), filter_clause)
    )
    nodes = gql(query, variables)["issues"]["nodes"]
    if not nodes:
        print("no issues match")
    for issue in nodes:
        print_issue_line(issue)


def cmd_teams(args):
    if args.key:
        team = fetch_team(args.key)
        print(f"{team['key']}  {team['name']}  id={team['id']}")
        cycle = team["activeCycle"]
        if cycle:
            print(f"active cycle: {cycle['number']} (ends {cycle['endsAt'][:10]}) id={cycle['id']}")
        print("states:")
        for state in sorted(team["states"]["nodes"], key=lambda s: s["name"]):
            print(f"  {state['name']} ({state['type']})  id={state['id']}")
        return
    data = gql("{ teams(first: 50) { nodes { id key name } } }")
    for team in data["teams"]["nodes"]:
        print(f"{team['key']}  {team['name']}  id={team['id']}")


def cmd_create(args):
    if not args.team:
        die("no team given. Pass --team KEY or set LINEAR_DEFAULT_TEAM.")
    team = fetch_team(args.team)
    issue_input = {
        "teamId": team["id"],
        "title": args.title,
        "stateId": resolve_state_id(team, args.state),
        "priority": args.priority,
    }
    if args.estimate is not None:
        issue_input["estimate"] = args.estimate
    if args.description:
        issue_input["description"] = args.description
    if args.assignee == "me":
        issue_input["assigneeId"] = viewer_id()
    if not args.no_cycle and team["activeCycle"]:
        issue_input["cycleId"] = team["activeCycle"]["id"]
    if args.parent:
        parent = gql(
            "query($id: String!) { issue(id: $id) { id } }", {"id": args.parent}
        )["issue"]
        issue_input["parentId"] = parent["id"]
    data = gql(
        """mutation($input: IssueCreateInput!) {
             issueCreate(input: $input) {
               success
               issue { identifier title url branchName }
             }
           }""",
        {"input": issue_input},
    )
    issue = data["issueCreate"]["issue"]
    print(f"created {issue['identifier']}: {issue['title']}")
    print(f"url: {issue['url']}")
    print(f"branch: {issue['branchName']}")


def cmd_update(args):
    issue = gql(
        "query($id: String!) { issue(id: $id) { id team { key } } }", {"id": args.id}
    )["issue"]
    update_input = {}
    if args.state:
        team = fetch_team(issue["team"]["key"])
        update_input["stateId"] = resolve_state_id(team, args.state)
    if args.title:
        update_input["title"] = args.title
    if args.description:
        update_input["description"] = args.description
    if args.priority is not None:
        update_input["priority"] = args.priority
    if args.estimate is not None:
        update_input["estimate"] = args.estimate
    if args.assignee:
        update_input["assigneeId"] = viewer_id() if args.assignee == "me" else args.assignee
    if not update_input:
        die("nothing to update — pass at least one of --state/--title/--description/--priority/--estimate/--assignee")
    data = gql(
        """mutation($id: String!, $input: IssueUpdateInput!) {
             issueUpdate(id: $id, input: $input) {
               success
               issue { identifier state { name } assignee { name } url }
             }
           }""",
        {"id": issue["id"], "input": update_input},
    )
    updated = data["issueUpdate"]["issue"]
    assignee = updated["assignee"]
    print(f"updated {updated['identifier']}: state={updated['state']['name']}"
          f" assignee={assignee['name'] if assignee else 'none'}")
    print(f"url: {updated['url']}")


def cmd_comment(args):
    issue = gql(
        "query($id: String!) { issue(id: $id) { id } }", {"id": args.id}
    )["issue"]
    comment_input = {"issueId": issue["id"], "body": args.body}
    data = gql(
        """mutation($input: CommentCreateInput!) {
             commentCreate(input: $input) { success comment { url } }
           }""",
        {"input": comment_input},
    )
    print(f"comment posted: {data['commentCreate']['comment']['url']}")


def cmd_query(args):
    variables = json.loads(args.variables) if args.variables else {}
    data = gql(args.graphql, variables)
    print(json.dumps(data, indent=2))


def main():
    parser = argparse.ArgumentParser(
        prog="linear.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("whoami", help="show the authenticated user and org").set_defaults(func=cmd_whoami)

    p = sub.add_parser("issue", help="full read of one issue: fields, description, comments")
    p.add_argument("id", help="issue identifier, e.g. ENG-123")
    p.set_defaults(func=cmd_issue)

    p = sub.add_parser("comments", help="just the comments of one issue")
    p.add_argument("id")
    p.set_defaults(func=cmd_comments)

    p = sub.add_parser("search", help="full-text search across issues")
    p.add_argument("term")
    p.add_argument("--team", help="restrict to a team key, e.g. ENG")
    p.add_argument("--limit", type=int, default=10)
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("list", help="list issues by assignee/team/state, newest-updated first")
    p.add_argument("--assignee", help="'me' or a person's name")
    p.add_argument("--team", help="team key, e.g. ENG")
    p.add_argument("--state", help="state name, e.g. 'In Development'")
    p.add_argument("--limit", type=int, default=15)
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("teams", help="list teams; pass a key for states + active cycle")
    p.add_argument("key", nargs="?")
    p.set_defaults(func=cmd_teams)

    p = sub.add_parser("create", help="create an issue (workspace defaults applied)")
    p.add_argument("--title", required=True)
    p.add_argument("--description")
    p.add_argument("--team", default=DEFAULT_TEAM_KEY)
    p.add_argument("--state", default=DEFAULT_STATE)
    p.add_argument("--priority", type=int, default=DEFAULT_PRIORITY, help="0 none, 1 urgent, 2 high, 3 medium, 4 low")
    p.add_argument("--estimate", type=int, help="story points; left unset when omitted")
    p.add_argument("--assignee", default="me", help="'me' (default) or 'none'")
    p.add_argument("--parent", help="parent issue identifier")
    p.add_argument("--no-cycle", action="store_true", help="skip adding to the active cycle")
    p.set_defaults(func=cmd_create)

    p = sub.add_parser("update", help="update fields on an issue")
    p.add_argument("id")
    p.add_argument("--state")
    p.add_argument("--title")
    p.add_argument("--description")
    p.add_argument("--priority", type=int)
    p.add_argument("--estimate", type=int)
    p.add_argument("--assignee", help="'me' or a user id")
    p.set_defaults(func=cmd_update)

    p = sub.add_parser("comment", help="post a comment on an issue")
    p.add_argument("id")
    p.add_argument("--body", required=True)
    p.set_defaults(func=cmd_comment)

    p = sub.add_parser("query", help="escape hatch: run raw GraphQL, prints JSON")
    p.add_argument("graphql")
    p.add_argument("--variables", help="JSON object of variables")
    p.set_defaults(func=cmd_query)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
