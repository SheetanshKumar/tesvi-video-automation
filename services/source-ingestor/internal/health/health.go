package health

import (
	"encoding/json"
	"net/http"
)

func Live(service string) http.HandlerFunc {
	return func(w http.ResponseWriter, _ *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		_ = json.NewEncoder(w).Encode(map[string]string{
			"status":  "ok",
			"service": service,
		})
	}
}

// Ready currently mirrors Live. Real readiness will check downstream
// dependencies (DB, Pub/Sub, external APIs) once they exist.
func Ready(service string) http.HandlerFunc {
	return Live(service)
}
