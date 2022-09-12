resource "google_service_account" "service_account" {
  account_id   = "horoscope-bot"
  display_name = "Horoscope Bot"
}

resource "google_project_iam_member" "service_account_publisher" {
  project = google_service_account.service_account.project
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.service_account.email}"

  condition {
    title      = "Cancer Topic"
    expression = "resource.name == '${google_pubsub_topic.horoscopes.id}'"
  }
}
