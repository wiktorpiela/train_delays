library("geosphere")
library("nominatimlite")
library("tidyverse")


get_station_coordinates <- function(data_path){
  
  data <- fs::dir_ls(data_path) %>% 
    map(.f = function(data_path) arrow::read_parquet(data_path))
  
  relacje <- character()
  stacje <- vector("list",length(data))
  
  for(x in seq_along(data)){
    
    relacje[x] <- unique(data[[x]]$Relacja)
    stacje[[x]] <- unique(data[[x]]$Stacja)
    
  }

  lon <- vector("list",length(stacje))
  lat <- vector("list",length(stacje))
  address <- vector("list",length(stacje))
  
  
  for(x in seq_along(stacje)){
    
    for(y in seq_along(stacje[[x]])){
      
      if(y==1){
        
        lon[[x]][y] <- geo_lite(stacje[[x]][y])$lon
        lat[[x]][y] <- geo_lite(stacje[[x]][y])$lat
        address[[x]][y] <- geo_lite(stacje[[x]][y])$address
        
      } else {
        
        if(stacje[[x]][y]=="Wierzbice Wrocławskie"){
          
          lon[[x]][y] <- 16.8384435
          lat[[x]][y] <- 50.9514547
          address[[x]][y] <- "Wierzbice Wro."
          
        } else{
          
          current_data <- geo_lite(stacje[[x]][y],limit=50) %>% filter(lon<90 & lon>-90)
          current_lon <- current_data$lon
          current_lat <- current_data$lat
          current_address <- current_data$address
          dist <- numeric()
          
          for(item in 1:nrow(current_data)){
            
            dist[item] <- distHaversine(c(as.numeric(current_lat[item]),as.numeric(current_lon[item])),
                                        c(as.numeric(lat[[x]][y-1]),as.numeric(lon[[x]][y-1]))
            )
            
          }
          
        }
        
        min_indx <- which.min(dist)
        lon[[x]][y] <- current_lon[min_indx]
        lat[[x]][y] <- current_lat[min_indx]
        address[[x]][y] <- current_address[min_indx]
        
      }
    }
    print(paste("Progress:",x/length(stacje)*100),"%")
  }
  
  corrdinates <- tibble(
    stacja = unlist(stacje),
    lon = unlist(lon),
    lat = unlist(lat),
    addr =unlist(address)
  ) %>%
    distinct()
  
  return(coordinates)

}