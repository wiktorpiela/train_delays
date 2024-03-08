const fileInput = document.querySelector(".file-input");
const reqUrl = "https://routes.googleapis.com/directions/v2:computeRoutes"
let gpsArray = [];
let rowArray = [];
let polylineArray = [];

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

    response.json().then(data => handleReceivedData(data))
}


getRoute(reqUrl, 51.111358, 15.293541, 51.266085, 15.569587)





// fileInput.addEventListener('change', () => {

//     const myFile = fileInput.files[0];
//     const reader = new FileReader()

//     reader.readAsText(myFile)

//     reader.onload = (event) => {

//         let csvdata = event.target.result
//         let rowdata = csvdata.split('\n')

//         for (let i = 1; i < rowdata.length - 1; i++) {
//             for (let j = 0; j < 4; j++){
//                 let row = rowdata[i].split(',')[j].replace(/\r/g, '');
//                 row = parseFloat(row)
//                 rowArray.push(row)
//             }
//             gpsArray.push(rowArray);
//             rowArray = [];
//         }

//         //console.log(gpsArray)
//         gpsArray.forEach((item) => {
//             console.log(item[0])
//         })
//     }
// })







// fetch(url, {
//     method: "POST",
//     headers: {
//         "Content-Type": "application/json",
//         "X-Goog-Api-Key": "AIzaSyCAau_6aJ3wCQ-IIp_PbSWLRDAmJ9bh6OU",
//         "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline"
//     },
//     body: JSON.stringify(reqBody)
// }).then((response) => {
//     return response.json();
// }).then((data) => {
//     if (data.hasOwnProperty("error")) {
//         console.log(data.error);
//     } else if (data.hasOwnProperty("routes")) {
//         console.log(data);
//     } else {
//         console.log("No routes found. Something might be wrong with request data");
//     }
// }).catch((error) => {
//     console.log(error)
// });