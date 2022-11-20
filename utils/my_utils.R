library("lubridate")
library("tidyverse")


draw_n_days_per_week <- function(start_day, end_day, n_day_per_week, n_day_per_week2=1){
  # the function randomizes the given number of days of the week from the range specified by the user, 
  # used to determine the days of data scraping
  # n_day_per_week  - how many days draw from week once it has 7 days
  # n_day_per_week2 - how many days draw from week once it has less days tha you put in n_day_per_week argument, 1 if not specified
  dates <- seq(as.Date(start_day),as.Date(end_day),"day")
  weeks <- format(dates, format="%W")
  
  df <- tibble(
    date=as.Date(dates),
    week=paste(weeks,"-",year(date))
  )
  
  all_weeks <- unique(df$week)
  
  dfy <- list()
  
  for(x in 1:length(all_weeks)){
    dfy[[x]] <- filter(df, week == all_weeks[x])
    if(nrow(dfy[[x]])>n_day_per_week){
      dfy[[x]] <- dfy[[x]][sample(nrow(dfy[[x]]),n_day_per_week),]
    } else {
      dfy[[x]] <- dfy[[x]][sample(nrow(dfy[[x]]),n_day_per_week2),]
    }
    
  }
  
  dfy <- reduce(dfy, bind_rows) %>% 
    mutate(weekday = weekdays(date)) %>% 
    arrange(date) 
  return(dfy)
}

load_and_prepare_data <- function(parent_dir){

  #gathering data, import each file, remove duplicates
  scraping_dirs <- list.files(parent_dir)
  scraping_dirs <- scraping_dirs[which(str_detect(scraping_dirs,"scraper_"))]
  
  subfolders <- character()
  
  for(x in seq_along(scraping_dirs)) subfolders[x] <- paste0(parent_dir,"\\",scraping_dirs[x],"\\data")
  
  all_files_path <- list()
  
  for(x in seq_along(subfolders)) all_files_path[[x]] <- fs::dir_ls(subfolders[x])
  
  all_files_path <- unlist(all_files_path)
  
  data <- lapply(all_files_path, arrow::read_parquet)  
  
  uni <- list()
  
  for(x in seq_along(data)){
    if(x==1){
      uni[[x]] <- data[[x]]
    } else {
      boolean <- logical()
      for(y in seq_along(uni)){
        boolean[y] <- identical(data[[x]],uni[[y]])
      }
      if(all(boolean==FALSE)){
        uni[[x]] <- data[[x]]
      }
    }
  }
  
  # dala processing, cleaning, data types, new features
  
  uni <- discard(uni, is_null)
  
  for(x in seq_along(uni)){

    uni[[x]] <- mutate(uni[[x]],
                       across(c(`Opóźnienie przyjazdu`,`Opóźnienie odjazdu`), parse_number),
                       across(c(`Przyjazd planowy`,`Odjazd planowy`), ~ dmy_hms(paste(Data,.))),
                       Data = dmy(Data),
                       n_stacje = row_number())
    
    if(tail(uni[[x]]$`Przyjazd planowy`,1)-uni[[x]]$`Odjazd planowy`[1]<0){
      
      for(y in 3:nrow(uni[[x]])){
        
        if(uni[[x]]$`Przyjazd planowy`[y] - uni[[x]]$`Przyjazd planowy`[y-1]<0){
          
          uni[[x]]$`Przyjazd planowy`[y] <- uni[[x]]$`Przyjazd planowy`[y]+86400
          
        } 
        
      }
      
      for(z in 2:(nrow(uni[[x]])-1)){
        
        if(uni[[x]]$`Odjazd planowy`[z] - uni[[x]]$`Odjazd planowy`[z-1]<0){
          
          uni[[x]]$`Odjazd planowy`[z] <- uni[[x]]$`Odjazd planowy`[z]+86400
          
        } 
        
      }
      
    }
    
    uni[[x]] <- mutate(uni[[x]],
                       dzien_tygodnia = weekdays(`Przyjazd planowy`),
                       miesiac = month(`Przyjazd planowy`),
                       planowy_postoj = `Odjazd planowy`-`Przyjazd planowy`,
                       planowy_czas_podrozy = max(`Przyjazd planowy`, na.rm=TRUE)-min(`Odjazd planowy`, na.rm=TRUE)
    )
  }
  
  return(uni)
}

prepare_raw_geo_dictionary <- function(data_path){
  
  data <- read_rds(data_path) #list of dataframes (direct output from load_and_prepare_data function)
  
  stacje <- vector("list",length(data))
  
  for(x in seq_along(data)) stacje[[x]] <- unique(data[[x]]$Stacja)
  
  uni_stacje <- unique(unlist(stacje))
  my_places <- nominatimlite::geo_lite(uni_stacje,limit=50)
  
  my_places <- my_places %>%
    add_row(query = "Wierzbice Wrocławskie",
            lat = 50.9514547,
            lon = 16.8384435,
            address = "Wierzbice Wrocławskie, Polska") %>%
    distinct()
  
  my_places <- filter(my_places, lon<90 & lon>-90)
  
  return(my_places)
}

get_station_coordinates <- function(data_path, geo_dict_path){
  
  data <- read_rds(data_path) #list of dataframes (direct output from load_and_prepare_data function)

  relacje <- character()
  stacje <- vector("list",length(data))
  
  for(x in seq_along(data)){
    
    relacje[x] <- unique(data[[x]]$Relacja)
    stacje[[x]] <- unique(data[[x]]$Stacja)
    
  }
  
  geo_dict <- read_rds(geo_dict_path)
  
  lon <- vector("list",length(stacje))
  lat <- vector("list",length(stacje))
  address <- vector("list",length(stacje))
  
  
  for(x in seq_along(stacje)){
    
    for(y in seq_along(stacje[[x]])){
      
      if(y==1){
        
        lon[[x]][y] <- filter(geo_dict, query==stacje[[x]][y])$lon
        lat[[x]][y] <- filter(geo_dict, query==stacje[[x]][y])$lat
        address[[x]][y] <- filter(geo_dict, query==stacje[[x]][y])$address
        
      } else {
        
        current_data <- filter(geo_dict, query==stacje[[x]][y])
        current_lon <- current_data$lon
        current_lat <- current_data$lat
        current_address <- current_data$address
        dist <- numeric()
        
        for(item in 1:nrow(current_data)){
          
          dist[item] <- geosphere::distHaversine(c(current_lat[item],current_lon[item]),
                                                 c(lat[[x]][y-1],lon[[x]][y-1])
          )
          
        }
        
        min_indx <- which.min(dist)
        lon[[x]][y] <- current_lon[min_indx]
        lat[[x]][y] <- current_lat[min_indx]
        address[[x]][y] <- current_address[min_indx]
        
      }
    }
  }
  
 return(list(stacje, lon, lat, address))
}