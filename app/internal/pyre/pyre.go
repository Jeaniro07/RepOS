// Package pyre compiles the Python-style regular expressions shared with the Python toolkit.
//
// Go's RE2 has no look-around and its \w is ASCII-only. Patterns used here avoid look-around;
// this package widens \w to Unicode letters, digits and underscore like Python 3 str patterns.
// \b stays ASCII-based in RE2, which only differs from Python next to non-ASCII letters.
package pyre

import (
	"regexp"
	"strings"
	"sync"
)

const word = `\p{L}\p{N}_`

// Translate rewrites \w and \W to their Unicode-aware equivalents.
func Translate(p string) string {
	var b strings.Builder
	inClass := false
	for i := 0; i < len(p); i++ {
		c := p[i]
		if c == '\\' && i+1 < len(p) {
			n := p[i+1]
			switch {
			case n == 'w' && inClass:
				b.WriteString(word)
			case n == 'w':
				b.WriteString("[" + word + "]")
			case n == 'W' && !inClass:
				b.WriteString("[^" + word + "]")
			default:
				b.WriteByte(c)
				b.WriteByte(n)
			}
			i++
			continue
		}
		if c == '[' && !inClass {
			inClass = true
		} else if c == ']' && inClass {
			inClass = false
		}
		b.WriteByte(c)
	}
	return b.String()
}

var (
	mu    sync.Mutex
	cache = map[string]*regexp.Regexp{}
)

// MustI compiles a case-insensitive Python-style pattern (cached).
func MustI(p string) *regexp.Regexp { return must("(?i)" + Translate(p)) }

// Must compiles a case-sensitive Python-style pattern (cached).
func Must(p string) *regexp.Regexp { return must(Translate(p)) }

// CompileI compiles a case-insensitive pattern and reports errors (for user-supplied lexicons).
func CompileI(p string) (*regexp.Regexp, error) { return regexp.Compile("(?i)" + Translate(p)) }

func must(p string) *regexp.Regexp {
	mu.Lock()
	defer mu.Unlock()
	if re, ok := cache[p]; ok {
		return re
	}
	re := regexp.MustCompile(p)
	cache[p] = re
	return re
}
