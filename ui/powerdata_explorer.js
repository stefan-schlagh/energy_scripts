async function main(){

    function selectElement(id, valueToSelect) {    
        let element = document.getElementById(id);
        element.value = valueToSelect;
    }

    function updateMonthSelection(year, month) {
        selectElement("year", year);
        selectElement("month", month);
    }

    updateMonthSelection(2024, 8);

    let year = 2024;
    let month = 8;

    let chart = await updateChart(null, year, month);

    document.getElementById('year').addEventListener('change', async (event) => {
        year = event.target.value;
        month = document.getElementById('month').value;
        console.log(`Year: ${year}, Month: ${month}`);

        chart = await updateChart(chart, year, month);
    });
    document.getElementById('month').addEventListener('change', async (event) => {
        year = document.getElementById('year').value;
        month = event.target.value;
        console.log(`Year: ${year}, Month: ${month}`);

        chart = await updateChart(chart, year, month);
    });
    let buttons = {
        'next_month': async (event) => {
            month++;
            if(month > 12) {
                year++;
                month = 1;
            }
            console.log(`Year: ${year}, Month: ${month}`);
            updateMonthSelection(year, month);
            chart = await updateChart(chart, year, month);
        },
        'prev_month': async (event) => {
            month--;
            if(month < 1) {
                year--;
                month = 12;
            }
            console.log(`Year: ${year}, Month: ${month}`);
            updateMonthSelection(year, month);
            chart = await updateChart(chart, year, month);
        }
    };

    document.getElementById('next_month').addEventListener('click', buttons.next_month);
    document.getElementById('prev_month').addEventListener('click', buttons.prev_month);
}

async function updateChart(chart, year, month){
    csv = await fetchPowerData(year, month);
    const data = parseData(csv);
    if (chart != null){
        chart.destroy();
    }
    return createChart(data);
}

async function fetchData(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
        throw new Error(`Response status: ${response.status}`);
        }

        return response.text();
    } catch (error) {
        console.error(error.message);
    }
}

async function fetchPowerData(year, month) {
    const url = `../data/power_averages_${year}_${month}.csv`;
    return await fetchData(url);
}

function parseData(csv) {
    const lines = csv.split('\n');
    const headers = lines[0].split(',');
    const data_lines = lines.slice(1);
    const data = [];

    for (let line of data_lines) {
        const values = line.split(',');
        data.push({
            hour: values[0], 
            grid_power_minus: parseInt(values[1]), 
            grid_power_plus: parseInt(values[2]), 
            house_power: parseInt(values[3]), 
            inverter_power: parseInt(values[4]) 
        })
    }
    return data;
}

function createChart(data) {
    // Prepare the data for Chart.js
    const labels = data.map(item => item.hour);
    const datasets = [
        {
            label: 'Power fed into the grid',
            data: data.map(item => item.grid_power_minus),
            borderColor: 'rgb(75, 192, 192)',
            tension: 0.1
        },
        {
            label: 'Power from the grid',
            data: data.map(item => item.grid_power_plus),
            borderColor: 'rgb(255, 99, 132)',
            tension: 0.1
        },
        {
            label: 'power used by the household',
            data: data.map(item => item.house_power),
            borderColor: 'rgb(255, 205, 86)',
            tension: 0.1
        },
        {
            label: 'power generated',
            data: data.map(item => item.inverter_power),
            borderColor: 'rgb(54, 162, 235)',
            tension: 0.1
        }
    ];

    // Create the chart
    const ctx = document.getElementById('powerChart').getContext('2d');
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Power Consumption Chart'
                },
                legend: {
                    position: 'top',
                }
            },
            scales: {
                x: {
                    ticks: {
                        maxRotation: 90,
                        minRotation: 90
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Power'
                    }
                }
            }
        }
    });
}

main()
    .then(text => {
        //console.log(text);
    })
    .catch(err => {
        if(err) console.error(err);
    });