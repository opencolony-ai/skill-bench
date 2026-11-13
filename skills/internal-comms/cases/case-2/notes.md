search team - week notes

- shipped typo-tolerant matching to all users on tuesday
- zero-result searches down from 8.4% to 5.9%
- p95 latency held at 180 ms even with the new matching
- interviewed 4 candidates for the open relevance engineer role, 1 offer out
- plan: A/B test the new ranking model on 10% of traffic starting monday; write the synonyms admin page
- problem: the click-log pipeline lost two days of data (tue-wed) after a schema change, so ranking evaluation for those days is unreliable
- problem: still one engineer short since september
