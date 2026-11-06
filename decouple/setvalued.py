"""Set-valued decision rule, parallel to decouple.model.decision (which is untouched).

Returns the smallest set of hypotheses whose posterior mass reaches `mass`,
with a per-member cytotoxicity veto.

Verdicts: nominate, shortlist, joint, abstain, and cytotoxic. A vetoed LEADING
single-driver member is a finding, not a filter step: the verdict is 'cytotoxic'
naming that compound, and we never fall through to the runner-up (that would
hand a chemist a false lead). Only non-leading vetoed members are dropped.
The leader is the higher-posterior of A/B; the rule applies when it is in the set.

Deliberate divergence from decouple.model.decision / selectivity: separability
is checked over REVEALED samples only (you can only exploit contrast you have
actually measured); the existing rules check every sample.
"""
import numpy as np

from decouple.model import HYPOTHESES

DEFAULT_TOX_CAP = 0.5


def set_decision(p_par, p_tox, samples, revealed, cfg, mass=0.95, names=('A', 'B')):
    p_par, p_tox = np.asarray(p_par, dtype=float), np.asarray(p_tox, dtype=float)
    cap = cfg.get('tox_cap', DEFAULT_TOX_CAP)
    order = [int(i) for i in np.argsort(-p_par, kind='stable')]
    lead = float(p_par[order[0]])

    def out(kind, cands, why, contrast, vetoed=()):
        idx = [HYPOTHESES.index(c) for c in cands]
        return {'kind': kind, 'candidates': list(cands), 'mass': float(sum(p_par[i] for i in idx)),
                'size': len(cands), 'vetoed': list(vetoed),
                'probability': float(p_par[idx[0]]) if idx else lead,
                'explanation': why, 'next_contrast': contrast}

    separates = lambda s: abs(s['x'][0] - s['x'][1]) > 1e-10
    untested = [s for s in samples if s['id'] not in revealed]
    best = max(untested, key=lambda s: abs(s['x'][0] - s['x'][1]), default=None)
    contrast = best['id'] if best is not None and separates(best) else None

    if not any(separates(s) for s in samples if s['id'] in revealed):
        return out('abstain', [], f'{names[0]} and {names[1]} have identical profiles in every assayed '
                   'specimen. No assay here can distinguish them.', contrast)

    chosen, cum = [], 0.0
    for i in order:
        chosen.append(i)
        cum += float(p_par[i])
        if cum >= mass:
            break
    leader = 0 if p_par[0] >= p_par[1] else 1
    if leader in chosen and p_tox[leader] > cap:
        L = HYPOTHESES[leader]
        return out('cytotoxic', [L], f'the compound best explaining the activity ({names[leader]}) also drives '
                   f'host-cell toxicity (P_tox={p_tox[leader]:.2f} > {cap}): a likely general cytotoxin, '
                   'not a selective lead \u2014 do not isolate it.', contrast, [L])
    vetoed = [HYPOTHESES[i] for i in chosen if i < 2 and p_tox[i] > cap]
    kept = [HYPOTHESES[i] for i in chosen if HYPOTHESES[i] not in vetoed]
    nm = dict(zip(HYPOTHESES, (names[0], names[1], 'both', 'neither')))
    veto_note = (f' Dropped as likely host-cytotoxic (P_tox > {cap}): '
                 + ', '.join(nm[v] for v in vetoed) + '.') if vetoed else ''

    if not kept or len(kept) == len(HYPOTHESES):
        why = ('The evidence does not narrow the explanation to a usable set.' if kept
               else 'Every plausible explanation was removed or none is supported.') + veto_note
        return out('abstain', [], why, contrast, vetoed)
    if kept == ['both']:
        return out('joint', kept, 'both contribute — fractionating will lose the activity; '
                   'do not isolate either alone.' + veto_note, contrast, vetoed)
    if len(kept) == 1 and kept[0] in ('A', 'B'):
        return out('nominate', kept, f'{nm[kept[0]]} is the single driver of the activity and is not the '
                   'host-cytotoxicity driver. Confirm with purified-compound assays.' + veto_note,
                   contrast, vetoed)
    labels = ' / '.join(nm[k] for k in kept)
    if set(kept) == {'A', 'B'}:
        why = (f'one of these two drives the activity; assaying an extract rich in {names[0]} but poor in '
               f'{names[1]} (or vice versa) would separate them.')
    else:
        why = (f'the activity is explained by one of: {labels}. An extract that varies these '
               'independently would narrow it further.')
    return out('shortlist', kept, why + veto_note, contrast, vetoed)
