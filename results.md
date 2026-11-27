# How federal appellate courts use § 230 precedent

## Citation count and network position

In the baseline network of 56 included opinions and 317 citation pairs, *Ben Ezra, Weinstein, & Co. v. America Online Inc.*, 206 F.3d 980 (10th Cir. 2000), ranks second by PageRank with ten incoming links. *Fair Housing Council v. Roommates.com*, 521 F.3d 1157 (9th Cir. 2008) (en banc), ranks sixth with 26. With damping set at 0.85, each citation passes along a share of the citing opinion’s PageRank divided by its outgoing citation count. The two opinions attract different kinds of support in this network. The table traces the largest contributions to each score. See the [edge contributions](data/precedent_citation_contributions.csv) and [passage records](data/citation_passages.csv).

| Cited opinion | Largest incoming contributions | Use in the citing opinion |
| --- | --- | --- |
| *Ben Ezra* | *Batzel v. Smith*, 0.0267, and *Green v. AOL*, 0.0196 | *Batzel* cites *Ben Ezra* when explaining the policy behind protecting hosts of third-party speech (CP-00009). *Green* cites it for protection of editorial and self-regulatory decisions (CP-00005). Each citing opinion links to two earlier opinions in the dataset. |
| *Roommates.com* | *Barnes v. Yahoo!*, 0.0036, and *Doe v. Internet Brands*, 0.0035 | *Barnes* draws on *Roommates.com* to define publication and qualify the reach of § 230(c)(1) (CP-00052, CP-00060). *Internet Brands* uses it to explain the statutory purpose before addressing a failure-to-warn duty (CP-00207). |

*Zeran* leads the baseline with a PageRank of 0.1909 and 31 incoming links. It also ranks first in all 500 simulations that keep each citing opinion’s outgoing citation count fixed and redraw its targets uniformly from earlier included opinions. Its simulated median score is 0.1703 and the central 95% range is 0.1566–0.1873. The observed score exceeds that range under this benchmark. The simulations account for the existence of earlier targets and how many citations each opinion makes. Citation age preferences, court-specific citation practices, and target popularity can also shape prominence. Scores describe the observed network. Binding authority depends on the issuing court, the forum, and the holding. See the [chronology comparison](data/pagerank_chronology.csv).

## Circuit citation distributions

Mean pairwise Jensen–Shannon divergence is 0.462 bits across 55 eligible circuit pairs in the pooled baseline. Each circuit contributes at least two citing opinions and five edges. The era comparison fixes the target set at the 29 opinions decided before the cutoff. Only the Second and Ninth Circuits meet the minimum threshold in both eras. Their divergence is 0.4286 before and 0.4294 from the cutoff onward. The Second and Ninth Circuits respectively contribute two and eight citing opinions and 13 and 34 edges in the earlier period. They contribute three and eleven citing opinions and 21 and 45 edges in the later period. No pair meets the strict threshold in both eras. The pooled result describes differences in citation distributions. The matched comparison supports a time comparison for one pair. Any claim of a doctrinal conflict requires examining holdings that resolve the same question. See the [matched era table](data/baseline_circuit_period_comparison.csv) and [annual estimates](data/circuit_divergence_annual.csv).

## Citation communities

Across 100 seeds, the undirected baseline produces two to four groups at resolution 0.75, four to six at 1.0, and five to eight at 1.25. At resolution 1.0 the reference partition has four groups, the consensus partition has eight, and the directed reference has five. The directed and undirected reference partitions have normalized mutual information of 0.808. The reference undirected partition has modularity 0.275, above the 97.5th percentile of 0.233 in the chronological benchmark. The benchmark asks whether the observed partition has more structure than uniform citation to earlier eligible opinions under each opinion’s observed citation count. See the [partition comparison](data/leiden_partition_comparison.csv) and [modularity benchmark](data/leiden_chronology.csv).

The undirected runs group *Chicago Lawyers’ Committee v. Craigslist*, *Backpage.com v. Dart*, and *Children’s Health Defense v. Meta* together in at least 99 of 100 runs for each pair at resolution 1.0. In the directed reference, *Dart* and *Children’s Health Defense* remain together and *Craigslist* is assigned to another group. The controlling passages explain why a single doctrinal label would obscure the links. *Dart* cites *Craigslist* in assessing intermediary liability (CP-00823). *Children’s Health Defense* distinguishes *Dart* in evaluating government coercion (CP-00824). The latter edge enters the baseline only. The baseline association between group and § 230(c)(1) outcome is exploratory. Its permutation result varies from p = .004 for the undirected reference partition to p = .050 for the consensus partition. The permutations do not condition on court, posture, or period. See [co-assignment](data/coassignment.csv) and [outcome associations](data/community_outcome_mi.csv).

## § 230(c)(1) outcomes by period

The primary comparison counts appellate rulings resolving § 230(c)(1) publisher treatment or third-party source for an underlying liability claim or theory. Opinions with both barred and unbarred theories enter the resolved denominator once as mixed. The broader comparison also counts controlling publisher-based § 230(e)(3) preemption determinations. It adds *StubHub*, *HomeAway*, and *Paxton*, each coded as declining to bar the disputed duty in the application before the court. The cutoff is April 11, 2018, and periods use opinion decision dates.

| Rule and period | All barred | None barred | Mixed | Outside resolved denominator | Resolved |
| --- | ---: | ---: | ---: | ---: | ---: |
| Primary, before cutoff | 17 | 4 | 2 | 6 | 23 |
| Primary, cutoff through study end | 8 | 8 | 3 | 8 | 19 |
| Broader, before cutoff | 17 | 5 | 2 | 5 | 24 |
| Broader, cutoff through study end | 8 | 10 | 3 | 6 | 21 |
| Primary, earlier equal-length window | 9 | 3 | 0 | 3 | 12 |
| Primary, later period excluding direct carveout opinions | 7 | 8 | 2 | 6 | 17 |

The all-barred share falls from 17 of 23 to 8 of 19 in the primary comparison and from 17 of 24 to 8 of 21 under the broader rule. Using equal-length windows gives 9 of 12 before and 8 of 19 after. Excluding direct carveout opinions gives 7 of 17 in the later period. The periods differ in the cases, legal theories, courts, and procedural postures they contain. The results describe the included opinions by period and do not identify an effect of FOSTA-SESTA. See the [period estimates](data/outcomes.csv) and [case-level assignments](data/publisher_outcome_comparison.csv).
