terraform {
  backend "gcs" {
    bucket = "horoscope-terraform-state"
  }

  required_providers {
    google = {
      version = "~> 4.48.0"
    }
  }
}

provider "google" {
  project = "prep-telegram-bots"
  region  = "europe-west3"
}
