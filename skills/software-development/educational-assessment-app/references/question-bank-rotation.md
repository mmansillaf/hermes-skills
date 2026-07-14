# Question Bank Rotation Strategy

## Problem

When writing multiple-choice questions sequentially, the correct answer naturally falls on position B (idx 1) roughly 70% of the time, and position D (idx 3) gets 0%. This makes the test predictable — test-takers can game it by guessing "B" on every question and scoring higher than chance.

## Solution — Circular Rotation

Rotate each question's options array and its correct index by a per-question shift so that correct answers distribute evenly across A, B, C, D (~25% each).

### Algorithm

```python
# For each question idx 0..N-1:
target = idx % 4                      # 0,1,2,3 cycling
shift = (target - current_correct) % 4

# Apply rotation:
new_options    = options[-shift:] + options[:-shift]     # circular shift
new_correct    = (current_correct + shift) % 4
```

### Generation Script (Python)

```python
import re
from collections import Counter

with open('assessment.html') as f:
    content = f.read()

match = re.search(r'const QUESTION_BANK = \[(.*?)\];', content, re.DOTALL)
block = match.group(1)
lines = block.strip().split('\n')

rotations = [0,0,0,2,0,0,0,1,3,0,1,1,3,3,2,2,3,0,1,2,3,0,1,2,0,0,2,2,0,0,
             1,2,3,0,2,3,3,1,1,2,0,1,0,2,3,0,0,2,3,0,1,2,3,0,0,2,3,0,1,2,3,0,1]

new_lines = []
q_idx = 0
for line in lines:
    stripped = line.strip()
    if stripped.startswith('//') or not stripped:
        new_lines.append(line)
        continue
    if stripped.startswith('{') and stripped.endswith('},'):
        opts_match = re.search(r"options:\[([^\]]+)\]", line)
        corr_match = re.search(r"correct:(\d+)", line)
        if opts_match and corr_match:
            opts_str = opts_match.group(1)
            corr = int(corr_match.group(1))
            rot = rotations[q_idx]
            if rot:
                opt_items = re.findall(r"'([^']*)'", opts_str)
                if len(opt_items) == 4:
                    new_opts = opt_items[-rot:] + opt_items[:-rot]
                    new_corr = (corr + rot) % 4
                    new_opts_str = ','.join(f"'{o}'" for o in new_opts)
                    line = line.replace(f'options:[{opts_str}]', f'options:[{new_opts_str}]')
                    line = line.replace(f'correct:{corr}', f'correct:{new_corr}')
            q_idx += 1
        new_lines.append(line)

# Verify
new_block = '\n'.join(new_lines)
corrects = re.findall(r'correct:(\d+)', new_block)
dist = Counter(int(c) for c in corrects)
print(dict(sorted(dist.items())))  # Should be ~{0:16, 1:16, 2:16, 3:15}
```

### In-Browser Audit

Paste this in the browser console after loading the app:

```js
(function(){var d={0:0,1:0,2:0,3:0};QB.forEach(function(q){d[q.correct]++});console.log(JSON.stringify(d))})()
```

Expected output: `{"0":16,"1":16,"2":16,"3":15}` (or similar, within ±2 of each other).

## Important

- Rotation preserves semantic correctness: all 4 options rotate together as a block
- The correct answer text stays the same, just moves to a different position
- This works for arrays of exactly 4 options. If you have 3 or 5 options, adjust the modulus and rotation logic accordingly
