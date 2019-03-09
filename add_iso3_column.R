library("dplyr")
library("tidyr")
library("purrr")
library("tidytext")
library("udpipe")
library("rvest")
library("textrank")
library("stopwords")
library("chunked")
library("furrr")
library("stringr")

TAGS_export01 <- data.table::fread(
    "~/Documents/bnl_data/TAGS_export01-newspapers1841-1878.csv")

to_iso <- function(country){
    case_when(str_detect(country, "Belgique") ~ "BEL",
              str_detect(country, "France") ~ "FRA",
              str_detect(country, "Allemagne") ~ "DEU",
              str_detect(country, "Prusse") ~ "DEU",
              str_detect(country, "Angleterre") ~ "GBR",
              TRUE ~ NA_character_)
}

plan(multiprocess, workers = 4)
TAGS_export01_v2 <- TAGS_export01 %>% 
    mutate(iso3 = future_map_chr(dc_title, to_iso))

readr::write_delim(TAGS_export01_v2, "TAGS_export01_v2.csv", delim = "|")
