# Skill: research

Fetch URLs and produce structured summaries. Use the `research_topic` tool when user wants to research a topic, summarize articles, or gather information from multiple sources.

## Tool: research_topic
Takes a topic, fetches relevant URLs (you provide URLs or it searches), and returns structured summary with bullets and sources.

Arguments:
- topic (string): Research topic
- urls (string[]): Optional list of URLs to fetch and summarize

Returns: { summary, sources[] }