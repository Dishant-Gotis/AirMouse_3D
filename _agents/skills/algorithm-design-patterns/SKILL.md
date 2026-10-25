---
skill_name: Algorithm Design Patterns
description: Master divide-and-conquer, greedy, dynamic programming, and backtracking approaches
category: Programming Paradigms
version: 1.0.0
---

# Algorithm Design Patterns

## Overview
Algorithm patterns provide frameworks for solving computational problems. Master major paradigms and when to apply them.

## Divide and Conquer

### Merge Sort

```javascript
function mergeSort(arr) {
  if (arr.length <= 1) return arr;

  const mid = Math.floor(arr.length / 2);
  const left = mergeSort(arr.slice(0, mid));
  const right = mergeSort(arr.slice(mid));

  return merge(left, right);
}

function merge(left, right) {
  const result = [];
  let i = 0, j = 0;

  while (i < left.length && j < right.length) {
    if (left[i] < right[j]) {
      result.push(left[i++]);
    } else {
      result.push(right[j++]);
    }
  }

  return result.concat(left.slice(i), right.slice(j));
}

// Time: O(n log n), Space: O(n)
console.log(mergeSort([3, 1, 4, 1, 5, 9])); // [1, 1, 3, 4, 5, 9]
```

### Binary Search

```javascript
function binarySearch(arr, target) {
  let left = 0, right = arr.length - 1;

  while (left <= right) {
    const mid = Math.floor((left + right) / 2);

    if (arr[mid] === target) {
      return mid;
    } else if (arr[mid] < target) {
      left = mid + 1;
    } else {
      right = mid - 1;
    }
  }

  return -1;
}

// Time: O(log n), Space: O(1)
console.log(binarySearch([1, 3, 5, 7, 9], 5)); // 2
```

## Greedy Algorithms

### Activity Selection

```javascript
function activitySelection(activities) {
  // Sort by end time
  activities.sort((a, b) => a.end - b.end);

  const selected = [activities[0]];

  for (let i = 1; i < activities.length; i++) {
    // If start time >= last activity's end time, select it
    if (activities[i].start >= selected[selected.length - 1].end) {
      selected.push(activities[i]);
    }
  }

  return selected;
}

const activities = [
  { name: 'A', start: 0, end: 6 },
  { name: 'B', start: 5, end: 9 },
  { name: 'C', start: 8, end: 11 },
  { name: 'D', start: 3, end: 5 },
  { name: 'E', start: 1, end: 2 }
];

// Greedy choice maximizes total activities
console.log(activitySelection(activities));
// [E, D, A, B, C]
```

### Huffman Coding

```javascript
class Node {
  constructor(char, freq, left = null, right = null) {
    this.char = char;
    this.freq = freq;
    this.left = left;
    this.right = right;
  }
}

function huffmanCoding(text) {
  // Count frequencies
  const freq = {};
  for (const char of text) {
    freq[char] = (freq[char] || 0) + 1;
  }

  // Create leaf nodes
  const heap = Object.entries(freq).map(
    ([char, f]) => new Node(char, f)
  );

  // Build tree
  while (heap.length > 1) {
    heap.sort((a, b) => a.freq - b.freq);
    const left = heap.shift();
    const right = heap.shift();
    const parent = new Node(null, left.freq + right.freq, left, right);
    heap.push(parent);
  }

  const root = heap[0];

  // Generate codes
  const codes = {};
  function traverse(node, code = '') {
    if (node.char !== null) {
      codes[node.char] = code;
    } else {
      traverse(node.left, code + '0');
      traverse(node.right, code + '1');
    }
  }

  traverse(root);
  return codes;
}

const codes = huffmanCoding('aab');
// { a: '0', b: '1' }
```

## Dynamic Programming

### Fibonacci with Memoization

```javascript
function fibonacci(n, memo = {}) {
  if (n in memo) return memo[n];
  if (n <= 1) return n;

  memo[n] = fibonacci(n - 1, memo) + fibonacci(n - 2, memo);
  return memo[n];
}

// Time: O(n), Space: O(n)
console.log(fibonacci(50)); // Much faster than recursion
```

### Longest Common Subsequence

```javascript
function longestCommonSubsequence(text1, text2) {
  const m = text1.length, n = text2.length;
  const dp = Array(m + 1).fill(null).map(() => Array(n + 1).fill(0));

  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (text1[i - 1] === text2[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1;
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
      }
    }
  }

  return dp[m][n];
}

// Time: O(m*n), Space: O(m*n)
console.log(longestCommonSubsequence('ace', 'abe')); // 2
```

### 0/1 Knapsack

```javascript
function knapsack(weights, values, capacity) {
  const n = weights.length;
  const dp = Array(capacity + 1).fill(0);

  for (let i = 0; i < n; i++) {
    for (let w = capacity; w >= weights[i]; w--) {
      dp[w] = Math.max(dp[w], dp[w - weights[i]] + values[i]);
    }
  }

  return dp[capacity];
}

// Time: O(n*capacity), Space: O(capacity)
const weights = [2, 3, 4];
const values = [3, 4, 5];
const capacity = 6;
console.log(knapsack(weights, values, capacity)); // 10
```

## Backtracking

### N-Queens Problem

```javascript
function solveNQueens(n) {
  const result = [];
  const board = Array(n).fill(null).map(() => Array(n).fill('.'));

  function isValid(row, col) {
    // Check column
    for (let i = 0; i < row; i++) {
      if (board[i][col] === 'Q') return false;
    }

    // Check diagonals
    for (let i = row - 1, j = col - 1; i >= 0 && j >= 0; i--, j--) {
      if (board[i][j] === 'Q') return false;
    }

    for (let i = row - 1, j = col + 1; i >= 0 && j < n; i--, j++) {
      if (board[i][j] === 'Q') return false;
    }

    return true;
  }

  function backtrack(row) {
    if (row === n) {
      result.push(board.map(r => r.join('')));
      return;
    }

    for (let col = 0; col < n; col++) {
      if (isValid(row, col)) {
        board[row][col] = 'Q';
        backtrack(row + 1);
        board[row][col] = '.';
      }
    }
  }

  backtrack(0);
  return result;
}

console.log(solveNQueens(4).length); // 2 solutions
```

### Word Search

```javascript
function wordSearch(board, word) {
  const rows = board.length;
  const cols = board[0].length;

  function dfs(row, col, index) {
    if (index === word.length) return true;

    if (row < 0 || row >= rows || col < 0 || col >= cols) {
      return false;
    }

    if (board[row][col] !== word[index]) {
      return false;
    }

    const temp = board[row][col];
    board[row][col] = '#'; // Mark as visited

    const found =
      dfs(row + 1, col, index + 1) ||
      dfs(row - 1, col, index + 1) ||
      dfs(row, col + 1, index + 1) ||
      dfs(row, col - 1, index + 1);

    board[row][col] = temp; // Restore

    return found;
  }

  for (let i = 0; i < rows; i++) {
    for (let j = 0; j < cols; j++) {
      if (dfs(i, j, 0)) {
        return true;
      }
    }
  }

  return false;
}

const board = [
  ['A', 'B', 'C', 'E'],
  ['S', 'F', 'C', 'S'],
  ['A', 'D', 'E', 'E']
];
console.log(wordSearch(board, 'ABCCED')); // true
```

## Production Checklist

- [ ] Identify problem type (divide-conquer, greedy, DP, backtracking)
- [ ] Analyze time and space complexity
- [ ] Implement with clear base cases
- [ ] Use memoization for DP problems
- [ ] Test with edge cases
- [ ] Optimize space when possible
- [ ] Document algorithm complexity
- [ ] Consider alternative approaches
- [ ] Profile hot paths
- [ ] Consider constraints (memory, time limits)
