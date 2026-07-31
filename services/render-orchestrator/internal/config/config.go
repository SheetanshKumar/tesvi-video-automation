package config

import "os"

type Config struct {
	Port string
}

func MustLoad() Config {
	return Config{
		Port: envOr("PORT", "8080"),
	}
}

func envOr(key, def string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return def
}
