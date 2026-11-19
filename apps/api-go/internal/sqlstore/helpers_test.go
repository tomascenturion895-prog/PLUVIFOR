package sqlstore

import (
	"strings"

	"github.com/tomascenturion895-prog/PLUVIFOR/apps/api-go/internal/station"
)

func stationFiltersMalicioso() station.Filters {
	return station.Filters{SourceCode: "x'; DROP TABLE stations;--", Zone: "x'", Text: "Ñandú"}
}

func containsAny(s string, subs ...string) bool {
	for _, sub := range subs {
		if strings.Contains(s, sub) {
			return true
		}
	}
	return false
}
