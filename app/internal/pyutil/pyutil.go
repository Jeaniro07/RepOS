// Package pyutil has small helpers that reproduce Python string semantics the checks rely on,
// so the Go app and the Python toolkit give the same answers on the same input.
package pyutil

import (
	"math"
	"strings"
	"unicode"
	"unicode/utf8"
)

// SplitLines splits like Python's str.splitlines() (no trailing empty line).
func SplitLines(s string) []string {
	var out []string
	start := 0
	for i := 0; i < len(s); {
		r, size := utf8.DecodeRuneInString(s[i:])
		switch r {
		case '\r':
			out = append(out, s[start:i])
			if i+1 < len(s) && s[i+1] == '\n' {
				i++
			}
			i++
			start = i
			continue
		case '\n', '\v', '\f', 0x1c, 0x1d, 0x1e, 0x85, 0x2028, 0x2029:
			out = append(out, s[start:i])
			i += size
			start = i
			continue
		}
		i += size
	}
	if start < len(s) {
		out = append(out, s[start:])
	}
	return out
}

// Strip removes any of chars from both ends (Python str.strip(chars)).
func Strip(s, chars string) string { return strings.Trim(s, chars) }

// Clip shortens text to n code points, ending with an ellipsis (Python _clip helper).
func Clip(text string, n int) string {
	r := []rune(text)
	if len(r) <= n {
		return text
	}
	return string(r[:n-1]) + "…"
}

// Len counts code points like Python len(str).
func Len(s string) int { return utf8.RuneCountInString(s) }

// IsUpperWord is Python str.isupper(): at least one cased char and no lowercase ones.
func IsUpperWord(s string) bool {
	cased := false
	for _, r := range s {
		if unicode.IsLower(r) || unicode.IsTitle(r) {
			return false
		}
		if unicode.IsUpper(r) {
			cased = true
		}
	}
	return cased
}

// FirstIsUpper is Python s[:1].isupper().
func FirstIsUpper(s string) bool {
	r, _ := utf8.DecodeRuneInString(s)
	return r != utf8.RuneError && unicode.IsUpper(r)
}

// HasDigit reports any Unicode decimal digit.
func HasDigit(s string) bool {
	for _, r := range s {
		if unicode.IsDigit(r) {
			return true
		}
	}
	return false
}

// Mean of xs (0 for empty).
func Mean(xs []float64) float64 {
	if len(xs) == 0 {
		return 0
	}
	t := 0.0
	for _, x := range xs {
		t += x
	}
	return t / float64(len(xs))
}

// PStdev is the population standard deviation (statistics.pstdev).
func PStdev(xs []float64) float64 {
	if len(xs) == 0 {
		return 0
	}
	m := Mean(xs)
	t := 0.0
	for _, x := range xs {
		t += (x - m) * (x - m)
	}
	return math.Sqrt(t / float64(len(xs)))
}

// Counter is an insertion-ordered counter (collections.Counter).
type Counter struct {
	keys  []string
	count map[string]int
}

// NewCounter returns an empty counter.
func NewCounter() *Counter { return &Counter{count: map[string]int{}} }

// Add increments key by n.
func (c *Counter) Add(key string, n int) {
	if _, ok := c.count[key]; !ok {
		c.keys = append(c.keys, key)
	}
	c.count[key] += n
}

// Get returns the count of key.
func (c *Counter) Get(key string) int { return c.count[key] }

// Len is the number of distinct keys.
func (c *Counter) Len() int { return len(c.keys) }

// Item is one key and its count.
type Item struct {
	Key   string
	Count int
}

// Items returns keys in insertion order.
func (c *Counter) Items() []Item {
	out := make([]Item, len(c.keys))
	for i, k := range c.keys {
		out[i] = Item{k, c.count[k]}
	}
	return out
}

// MostCommon sorts by count descending, ties in insertion order (Counter.most_common()).
func (c *Counter) MostCommon() []Item {
	items := c.Items()
	// stable insertion sort by count desc keeps ties in insertion order
	for i := 1; i < len(items); i++ {
		for j := i; j > 0 && items[j].Count > items[j-1].Count; j-- {
			items[j], items[j-1] = items[j-1], items[j]
		}
	}
	return items
}
