package civil

import (
	"encoding/json"
	"testing"
)

func TestParseYSerializa(t *testing.T) {
	d, err := Parse("2026-10-31")
	if err != nil {
		t.Fatal(err)
	}
	b, _ := json.Marshal(d)
	if string(b) != `"2026-10-31"` {
		t.Fatalf("JSON = %s", b)
	}
	var back Date
	if err := json.Unmarshal(b, &back); err != nil || !back.Equal(d) {
		t.Fatalf("ida y vuelta falló: %v %v", back, err)
	}
}

func TestParseRechazaEntradasInvalidas(t *testing.T) {
	for _, s := range []string{"", "2026-13-01", "2026-02-30", "31/10/2026", "2026-1-5", "2026-10-31T00:00:00"} {
		if _, err := Parse(s); err == nil {
			t.Errorf("Parse(%q) debía fallar", s)
		}
	}
}

func TestAritmetica(t *testing.T) {
	a, _ := Parse("2015-09-20")
	b, _ := Parse("2016-06-26")
	if got := a.DaysTo(b) + 1; got != 281 {
		t.Fatalf("días del tramo = %d, quería 281", got)
	}
	if got := a.AddDays(1).String(); got != "2015-09-21" {
		t.Fatalf("AddDays = %s", got)
	}
	if !a.Before(b) || !b.After(a) || a.Equal(b) {
		t.Fatal("comparaciones incorrectas")
	}
}
