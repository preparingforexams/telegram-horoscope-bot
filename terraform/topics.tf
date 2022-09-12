resource "google_pubsub_topic" "horoscopes" {
  name                       = "horoscopes"
  message_retention_duration = "86400s"
}
