// Package report holds findings, tiers, waivers and report rendering shared by every check.
//
// Tiers (borrowed in spirit from Nutlope/hallmark):
//
//	FLOOR  - never ships. Fix it. Not waivable.
//	REFLEX - a default that reads as generated. Fix it, or waive it on the record
//	         with a real reason (waivers.json).
//	FINISH - craft note. Answer it; never blocks delivery.
package report

import (
	"bytes"
	"encoding/json"
	"fmt"
	"math"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
)

const (
	Floor  = "FLOOR"
	Reflex = "REFLEX"
	Finish = "FINISH"
)

// Exit codes used by the CLI.
const (
	ExitClean  = 0
	ExitFloor  = 1
	ExitReflex = 2
	ExitUsage  = 3
)

var tierOrder = map[string]int{Floor: 0, Reflex: 1, Finish: 2}

// Finding is one measured problem. Optional fields are nil when absent (JSON null).
type Finding struct {
	Gate         string  `json:"gate"`
	Tier         string  `json:"tier"`
	Message      string  `json:"message"`
	At           *string `json:"at"`
	Fix          *string `json:"fix"`
	Evidence     *string `json:"evidence"`
	Waived       bool    `json:"waived"`
	WaiverReason *string `json:"waiver_reason"`
}

// New builds a finding; at and fix may be "" for none.
func New(gate, tier, message, at, fix string) Finding {
	return Finding{Gate: gate, Tier: tier, Message: message, At: opt(at), Fix: opt(fix)}
}

func opt(s string) *string {
	if s == "" {
		return nil
	}
	return &s
}

func deref(s *string) string {
	if s == nil {
		return ""
	}
	return *s
}

// AtString returns the location or "".
func (f Finding) AtString() string { return deref(f.At) }

// FixString returns the fix or "".
func (f Finding) FixString() string { return deref(f.Fix) }

// Label is the short status shown in the Markdown table.
func (f Finding) Label() string {
	if f.Waived {
		return "WAIVED"
	}
	switch f.Tier {
	case Floor:
		return "FAIL"
	case Reflex:
		return "REFLEX"
	}
	return "NOTE"
}

// Report collects findings and measurements for one subject.
type Report struct {
	Subject      string
	Kind         string
	Findings     []Finding
	Metrics      *Metrics
	ManualChecks []string
}

// NewReport starts an empty report.
func NewReport(subject, kind string) *Report {
	return &Report{Subject: subject, Kind: kind, Metrics: NewMetrics()}
}

// Add appends findings.
func (r *Report) Add(items ...Finding) { r.Findings = append(r.Findings, items...) }

// Sorted returns findings ordered by tier, gate, location.
func (r *Report) Sorted() []Finding {
	out := append([]Finding(nil), r.Findings...)
	sort.SliceStable(out, func(i, j int) bool {
		a, b := out[i], out[j]
		if tierOrder[a.Tier] != tierOrder[b.Tier] {
			return tierOrder[a.Tier] < tierOrder[b.Tier]
		}
		if a.Gate != b.Gate {
			return a.Gate < b.Gate
		}
		return a.AtString() < b.AtString()
	})
	return out
}

// OpenFloor lists FLOOR findings (never waivable).
func (r *Report) OpenFloor() []Finding {
	var out []Finding
	for _, f := range r.Findings {
		if f.Tier == Floor {
			out = append(out, f)
		}
	}
	return out
}

// OpenReflex lists REFLEX findings that are not waived.
func (r *Report) OpenReflex() []Finding {
	var out []Finding
	for _, f := range r.Findings {
		if f.Tier == Reflex && !f.Waived {
			out = append(out, f)
		}
	}
	return out
}

// ExitCode: 1 with any FLOOR, 2 with open REFLEX, else 0.
func (r *Report) ExitCode() int {
	if len(r.OpenFloor()) > 0 {
		return ExitFloor
	}
	if len(r.OpenReflex()) > 0 {
		return ExitReflex
	}
	return ExitClean
}

// Verdict is the one-line outcome.
func (r *Report) Verdict() string {
	switch r.ExitCode() {
	case ExitFloor:
		return "BLOCKED: fix every FLOOR failure before anyone sees this."
	case ExitReflex:
		return "NOT YET: fix or waive (with a reason) every open REFLEX finding."
	}
	return "CLEAR: no open FLOOR or REFLEX findings. Still review it with fresh eyes."
}

// Counts per tier.
type Counts struct {
	Floor        int `json:"floor"`
	ReflexOpen   int `json:"reflex_open"`
	ReflexWaived int `json:"reflex_waived"`
	Finish       int `json:"finish"`
}

// Counts tallies findings by tier.
func (r *Report) Counts() Counts {
	var c Counts
	for _, f := range r.Findings {
		switch {
		case f.Tier == Floor:
			c.Floor++
		case f.Tier == Reflex && f.Waived:
			c.ReflexWaived++
		case f.Tier == Reflex:
			c.ReflexOpen++
		default:
			c.Finish++
		}
	}
	return c
}

type jsonReport struct {
	Subject      string   `json:"subject"`
	Kind         string   `json:"kind"`
	Verdict      string   `json:"verdict"`
	ExitCode     int      `json:"exit_code"`
	Counts       Counts   `json:"counts"`
	Metrics      *Metrics `json:"metrics"`
	Findings     []Finding `json:"findings"`
	ManualChecks []string `json:"manual_checks"`
}

// MarshalJSON renders the same shape as the Python toolkit.
func (r *Report) MarshalJSON() ([]byte, error) {
	f := r.Sorted()
	if f == nil {
		f = []Finding{}
	}
	mc := r.ManualChecks
	if mc == nil {
		mc = []string{}
	}
	return marshal(jsonReport{r.Subject, r.Kind, r.Verdict(), r.ExitCode(), r.Counts(), r.Metrics, f, mc})
}

// JSON returns indented JSON without HTML escaping.
func (r *Report) JSON() string {
	b, err := marshalIndent(r)
	if err != nil {
		return "{}"
	}
	return string(b)
}

// Markdown renders the human report.
func (r *Report) Markdown() string {
	c := r.Counts()
	var b strings.Builder
	w := func(s string) { b.WriteString(s); b.WriteByte('\n') }
	w(fmt.Sprintf("# slopguard %s report", r.Kind))
	w("")
	w(fmt.Sprintf("- Subject: `%s`", r.Subject))
	w(fmt.Sprintf("- Verdict: **%s**", r.Verdict()))
	w(fmt.Sprintf("- Floor %d FAIL · Reflex %d open (%d waived) · Finish %d notes", c.Floor, c.ReflexOpen, c.ReflexWaived, c.Finish))
	w("")
	if r.Metrics.Len() > 0 {
		w("## Measured")
		w("")
		for _, kv := range r.Metrics.items {
			w(fmt.Sprintf("- %s: %s", kv.Key, FormatValue(kv.Value)))
		}
		w("")
	}
	if len(r.Findings) > 0 {
		w("## Findings")
		w("")
		w("| | Gate | Where | Problem | Fix |")
		w("|---|---|---|---|---|")
		for _, f := range r.Sorted() {
			problem := f.Message
			if f.Waived {
				problem += fmt.Sprintf(" _(waived: %s)_", deref(f.WaiverReason))
			}
			if f.Evidence != nil {
				problem += fmt.Sprintf(" — `%s`", *f.Evidence)
			}
			at := f.AtString()
			if at == "" {
				at = "-"
			}
			w(fmt.Sprintf("| %s | `%s` | %s | %s | %s |", f.Label(), f.Gate, at, cell(problem), cell(f.FixString())))
		}
		w("")
	} else {
		w("No findings.")
		w("")
	}
	if len(r.ManualChecks) > 0 {
		w("## Not measurable here: check by eye/ear and say so")
		w("")
		for _, m := range r.ManualChecks {
			w("- [ ] " + m)
		}
		w("")
	}
	w("_A measured pass is not a good video. Numbers catch what is broken; a fresh-context " +
		"critic catches what is weak. Report what was measured and what nobody checked._")
	return b.String()
}

func cell(s string) string {
	return strings.ReplaceAll(strings.ReplaceAll(s, "|", "\\|"), "\n", " ")
}

// FormatValue mirrors the Python report: floats with 2 decimals, lists joined, "none" for empty.
func FormatValue(v any) string {
	switch x := v.(type) {
	case float64:
		return strconv.FormatFloat(x, 'f', 2, 64)
	case float32:
		return strconv.FormatFloat(float64(x), 'f', 2, 64)
	case []float64:
		if len(x) == 0 {
			return "none"
		}
		parts := make([]string, len(x))
		for i, f := range x {
			parts[i] = FormatValue(f)
		}
		return strings.Join(parts, ", ")
	case []string:
		if len(x) == 0 {
			return "none"
		}
		return strings.Join(x, ", ")
	case []any:
		if len(x) == 0 {
			return "none"
		}
		parts := make([]string, len(x))
		for i, f := range x {
			parts[i] = FormatValue(f)
		}
		return strings.Join(parts, ", ")
	case bool:
		if x {
			return "True"
		}
		return "False"
	case nil:
		return "None"
	}
	return fmt.Sprint(v)
}

// Round rounds half to even, like Python's round().
func Round(x float64, digits int) float64 {
	p := math.Pow(10, float64(digits))
	return math.RoundToEven(x*p) / p
}

// ---------------------------------------------------------------- waivers

// Waiver silences one REFLEX gate on the record.
type Waiver struct {
	Gate   string
	Reason string
	At     *string
}

// LoadWaivers reads a JSON list (or {"waivers": [...]}) of {"gate","reason","at"?}.
// A waiver whose reason is shorter than 8 characters is not a waiver.
func LoadWaivers(path string) ([]Waiver, error) {
	if path == "" {
		return nil, nil
	}
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, nil
		}
		return nil, err
	}
	var raw any
	if err := json.Unmarshal(bytes.TrimPrefix(data, []byte("\xef\xbb\xbf")), &raw); err != nil {
		return nil, fmt.Errorf("%s: %w", path, err)
	}
	var items []any
	switch x := raw.(type) {
	case map[string]any:
		items, _ = x["waivers"].([]any)
	case []any:
		items = x
	}
	var out []Waiver
	for _, it := range items {
		m, ok := it.(map[string]any)
		if !ok {
			continue
		}
		gate, _ := m["gate"].(string)
		if gate == "" {
			continue
		}
		reason := strings.TrimSpace(fmt.Sprint(nz(m["reason"])))
		if len([]rune(reason)) < 8 {
			continue
		}
		w := Waiver{Gate: gate, Reason: reason}
		if at, ok := m["at"]; ok && at != nil {
			s := pyStr(at)
			w.At = &s
		}
		out = append(out, w)
	}
	return out, nil
}

func nz(v any) any {
	if v == nil {
		return ""
	}
	return v
}

// pyStr renders a JSON scalar the way Python's str() would for the "at" field.
func pyStr(v any) string {
	if f, ok := v.(float64); ok {
		if f == math.Trunc(f) && math.Abs(f) < 1e15 {
			return strconv.FormatFloat(f, 'f', 1, 64)
		}
		return strconv.FormatFloat(f, 'g', -1, 64)
	}
	return fmt.Sprint(v)
}

// ApplyWaivers marks matching REFLEX findings as waived. FLOOR is never waivable.
func ApplyWaivers(r *Report, waivers []Waiver) {
	for i := range r.Findings {
		f := &r.Findings[i]
		if f.Tier != Reflex {
			continue
		}
		for _, w := range waivers {
			if w.Gate != f.Gate {
				continue
			}
			if w.At != nil && !atMatches(*w.At, f.At) {
				continue
			}
			f.Waived = true
			reason := w.Reason
			f.WaiverReason = &reason
			break
		}
	}
}

func atMatches(want string, have *string) bool {
	if have == nil {
		return false
	}
	a, err1 := strconv.ParseFloat(strings.TrimRight(want, "s"), 64)
	b, err2 := strconv.ParseFloat(strings.TrimRight(strings.SplitN(*have, "-", 2)[0], "s"), 64)
	if err1 != nil || err2 != nil {
		return strings.TrimSpace(want) == strings.TrimSpace(*have)
	}
	return math.Abs(a-b) <= 0.75
}

// WriteOutputs writes <stem>.md and <stem>.json into outDir (when set).
func WriteOutputs(r *Report, outDir, stem string) ([]string, error) {
	if outDir == "" {
		return nil, nil
	}
	if err := os.MkdirAll(outDir, 0o755); err != nil {
		return nil, err
	}
	md := filepath.Join(outDir, stem+".md")
	js := filepath.Join(outDir, stem+".json")
	if err := os.WriteFile(md, []byte(r.Markdown()), 0o644); err != nil {
		return nil, err
	}
	if err := os.WriteFile(js, []byte(r.JSON()), 0o644); err != nil {
		return nil, err
	}
	return []string{md, js}, nil
}

// ---------------------------------------------------------------- ordered metrics

type kv struct {
	Key   string
	Value any
}

// Metrics is an insertion-ordered map (Python dict semantics).
type Metrics struct{ items []kv }

// NewMetrics returns an empty ordered map.
func NewMetrics() *Metrics { return &Metrics{} }

// Set inserts or replaces a value, keeping the first insertion position.
func (m *Metrics) Set(key string, value any) {
	for i := range m.items {
		if m.items[i].Key == key {
			m.items[i].Value = value
			return
		}
	}
	m.items = append(m.items, kv{key, value})
}

// Get returns a value and whether it exists.
func (m *Metrics) Get(key string) (any, bool) {
	for _, it := range m.items {
		if it.Key == key {
			return it.Value, true
		}
	}
	return nil, false
}

// Len is the number of keys.
func (m *Metrics) Len() int {
	if m == nil {
		return 0
	}
	return len(m.items)
}

// Each visits keys in insertion order.
func (m *Metrics) Each(fn func(key string, value any)) {
	for _, it := range m.items {
		fn(it.Key, it.Value)
	}
}

// MarshalJSON keeps insertion order.
func (m *Metrics) MarshalJSON() ([]byte, error) {
	var b bytes.Buffer
	b.WriteByte('{')
	for i, it := range m.items {
		if i > 0 {
			b.WriteByte(',')
		}
		k, _ := marshal(it.Key)
		v, err := marshal(it.Value)
		if err != nil {
			return nil, err
		}
		b.Write(k)
		b.WriteByte(':')
		b.Write(v)
	}
	b.WriteByte('}')
	return b.Bytes(), nil
}

func marshal(v any) ([]byte, error) {
	var b bytes.Buffer
	enc := json.NewEncoder(&b)
	enc.SetEscapeHTML(false)
	if err := enc.Encode(v); err != nil {
		return nil, err
	}
	return bytes.TrimRight(b.Bytes(), "\n"), nil
}

func marshalIndent(v any) ([]byte, error) {
	raw, err := marshal(v)
	if err != nil {
		return nil, err
	}
	var out bytes.Buffer
	if err := json.Indent(&out, raw, "", "  "); err != nil {
		return nil, err
	}
	return out.Bytes(), nil
}

// MarshalIndent exposes the HTML-safe-off indented encoder to other packages.
func MarshalIndent(v any) ([]byte, error) { return marshalIndent(v) }
