const fileInput = document.querySelector(".file-input");
const reqUrl = "https://routes.googleapis.com/directions/v2:computeRoutes"
let rowArray = [];
let gpsArray = [];
let routesEncodedArray = [];
let routesDistanceArray = [];
let routesDurationArray = [];
let outputArray = [];

function downloadCSV(array, filename) {

    const csvContent = array.map(row => row.join('###MYRANDOMDELIMITER###')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', filename);

    document.body.appendChild(link);

    link.click();

    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

function download1DArray(array, filename) {
    const arrayAsString = array.join('\n');
    const blob = new Blob([arrayAsString], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');

    link.setAttribute('href', url);
    link.setAttribute('download', filename);

    document.body.appendChild(link);

    link.click();

    document.body.removeChild(link);
    URL.revokeObjectURL(url);
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

    try {

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

            let encodedPolylineStr;
            let distanceRouteStr;
            let durationRouteStr;

            if (data.hasOwnProperty("routes")) {
                encodedPolylineStr = data.routes[0].polyline.encodedPolyline
                distanceRouteStr = data.routes[0].distanceMeters
                durationRouteStr = data.routes[0].duration
            } else {
                encodedPolylineStr = ''
                distanceRouteStr = ''
                durationRouteStr = ''
            }

            routesEncodedArray.push(encodedPolylineStr)
            routesDistanceArray.push(distanceRouteStr)
            routesDurationArray.push(durationRouteStr)

        })

    } catch (error) {
        console.log('Error fetching route:', error);
        routesEncodedArray.push('');
        routesDistanceArray.push('');
        routesDurationArray.push('');
    }
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

        let output;
        gpsArray.forEach((item) => {
            output = getRoute(reqUrl, item[0], item[1], item[2], item[3])

        })

        setTimeout(() => {

            // for (let i = 0; i < gpsArray.length; i++) {

            //     rowArray.push(gpsArray[i][0])
            //     rowArray.push(gpsArray[i][1])
            //     rowArray.push(gpsArray[i][2])
            //     rowArray.push(gpsArray[i][3])

            //     rowArray.push(routesEncodedArray[i])
            //     rowArray.push(routesDistanceArray[i])
            //     rowArray.push(routesDurationArray[i])

            //     outputArray.push(rowArray);
            //     rowArray = [];
            // }

            // downloadCSV(outputArray, 'encodedPolylines.csv');

            // console.log(routesEncodedArray)
            // console.log(routesDistanceArray)
            // console.log(routesDurationArray)

            download1DArray(routesEncodedArray, 'encodedPolylines.csv')
            download1DArray(routesDistanceArray, 'routesDistance.csv')
            download1DArray(routesDurationArray, 'routesDuration.csv')

        }, 200000)

    }
})






