const fileInput = document.querySelector(".file-input");
const reqUrl = "https://routes.googleapis.com/directions/v2:computeRoutes"
let rowArray = [];
let gpsArray = [];
let routesEncodedArray = [];
let routesDistance = [];
let routesDuration = [];

function handleReceivedData(inputData) {
    // const header = Object.keys(inputData).toString();
    // const routeDistance = inputData.distanceMeters
    // const routeDuration = inputData.durationRoute
    // const routePolyline = inputData.polyline.encPolyline

    polylineArray.push(inputData)



    // let dataText = []

    // for(i=0; i < modified.length; i++){
    //     line = `${modified[i]},${original[i]}`
    //     dataText.push(line)
    // }

    // dataText = dataText.join('\n')

    // const csv = [header, dataText].join('\n');
    // startCSVDownload(csv)
}

function startCSVDownload(input) {
    const blob = new Blob([input], { type: 'application/csv' });
    const url = URL.createObjectURL(blob);

    const getFile = document.createElement('a');
    getFile.download = 'routes-output.csv';
    getFile.href = url;
    getFile.style.display = 'none';

    document.body.appendChild(getFile);

    getFile.click();
    getFile.remove();
    URL.revokeObjectURL(url);
}

const getRoute = async (url, latitudeA, longitudeA, latitudeB, longitudeB) => {

    const reqBody = {
        "origin": {
            "location": {
                "latLng": {
                    "latitude": latitudeA,
                    "longitude": longitudeA
                }
            }
        },
        "destination": {
            "location": {
                "latLng": {
                    "latitude": latitudeB,
                    "longitude": longitudeB
                }
            }
        },
        "travelMode": "TRANSIT",
        "transitPreferences": {
            allowedTravelModes: ["TRAIN"]
        }
    };

    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": "MY_KEY",
            "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline"
        },
        body: JSON.stringify(reqBody)
    })

    response.json().then(data => {
        if (data.hasOwnProperty("routes")) {
            encodedPoyline = data.routes[0].polyline.encodedPolyline
            distanceRoute = data.routes[0].distanceMeters
            durationRoute = data.routes[0].duration
        } else {
            encodedPoyline = ''
            distanceRoute = ''
            durationRoute = ''
        }

        routesEncodedArray.push(encodedPoyline)
        routesDistance.push(distanceRoute)
        routesDuration.push(durationRoute)
    })
}

fileInput.addEventListener('change', () => {

    const myFile = fileInput.files[0];
    const reader = new FileReader()

    reader.readAsText(myFile)

    reader.onload = (event) => {

        let csvdata = event.target.result
        let rowdata = csvdata.split('\n')

        for (let i = 1; i < rowdata.length - 1; i++) {
            for (let j = 0; j < 4; j++) {
                let row = rowdata[i].split(',')[j].replace(/\r/g, '');
                row = parseFloat(row)
                rowArray.push(row)
            }
            gpsArray.push(rowArray);
            rowArray = [];
        }

        //console.log(gpsArray)


        gpsArray.forEach((item) => {
            getRoute(reqUrl, item[0], item[1], item[2], item[3])
        })

        console.log(gpsArray)
        console.log(routesEncodedArray)
        console.log(routesDistance)
        console.log(routesDuration)

    }
})






