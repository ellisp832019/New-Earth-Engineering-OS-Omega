# Impact Classification

The impact engine uses conservative categories so comparisons stay predictable.

## Classification buckets

- `low` - limited overlap or weak coupling
- `moderate` - meaningful shared surface area
- `high` - strong coupling, identity conflict, or broad shared contract surface
- `unknown` - insufficient evidence for a reliable score

## Signals used

- shared contract types
- identity alignment or conflict
- dependency proximity
- contract drift presence
- peer repository similarity

## Rule of thumb

If the evidence is weak, the analysis should remain cautious rather than overconfident.
