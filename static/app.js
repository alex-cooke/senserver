(function() {

    var app = angular.module('app', []);

    //  Dashboard Directive

    app.directive('dashboard', function() {

        return {
            restrict: 'E',
            templateUrl: '/static/dashboard.html',
            controllerAs: '$ctrl',
            controller: ['$http', '$interval', function($http, $interval) {
                var $ctrl = this;

                $ctrl.refreshInterval = 250;


                function setStartAndEndTime(interval) {
                    $ctrl.startTime = moment().add(interval, -1);
                    $ctrl.lastEndTime = $ctrl.endTime || moment();
                    $ctrl.endTime = moment();
                    
                }

                $ctrl.init = function() {

                    setStartAndEndTime('minute');

                    //  Get the initial data range (1 minute)
                    $http.get('/sense/range',
                        {
                            params: {
                                startTime: $ctrl.startTime.format('YYYY-MM-DD HH:mm:ss'),
                                endTime: $ctrl.endTime.format('YYYY-MM-DD HH:mm:ss')
                            }
                        })
                        .then(function (data) {

                            //  Transform and save the data
                            $ctrl.rangeData = _(data.data)
                                .map(function(d) {
                                    return {
                                        time: new moment(d[0]).toDate(),
                                        temperature: d[1],
                                        pressure: d[2],
                                        humidity: d[3]
                                    }
                                }).value();

                            //  Render the Chart
                            renderChart($ctrl.rangeData, $('#lineChart'));

                            //  Start getting current data
                            $interval($ctrl.refresh, $ctrl.refreshInterval);

                        });

                }

                $ctrl.refresh = function () {

                    //  get the current data
                    $http.get('/sense/current').then(function (data) {
                        
                        setStartAndEndTime('minute');

                        //  parse the date
                        var current = data.data;
                        current.time = moment(current.time).toDate();
                        
                        $ctrl.current = data.data;

                        $ctrl.rangeData.push($ctrl.current);

                        rerenderChart($ctrl.rangeData, $('#lineChart'));
                    });

                }

                //  define the chart scales
                var scale = {
                    time: d3.scaleTime(),
                    humidity: d3.scaleLinear().domain([0, 100]),
                    temperature: d3.scaleLinear().domain([0, 65]),
                    pressure: d3.scaleLinear().domain([0, 2000]),
                    pitch: d3.scaleLinear().domain([0, 360])
                };

                //  define line functions for temperature, humidity and pressure
                var lines = {
                    humidity: d3.line()
                        .x(function (d) { return scale.time(d.time); })
                        .y(function (d) { return scale.humidity(d.humidity); }),
                    temperature: d3.line()
                        .x(function (d) { return scale.time(d.time); })
                        .y(function (d) { return scale.temperature(d.temperature); }),
                    pressure: d3.line()
                        .x(function (d) { return scale.time(d.time); })
                        .y(function (d) { return scale.pressure(d.pressure); }),
                    pitch: d3.line()
                        .x(function (d) { return scale.time(d.time); })
                        .y(function (d) { return scale.pitch(d.pitch); })
            }


                //  Render the line charts
                function renderChart(data, $svg) {

                    //  Generate the scales
                    var width = $svg.width(), height = $svg.height();
                    _(lines)
                        .each(function(lineFunction, lineName) {
                            scale[lineName].range([height, 0]);
                        });

                    scale.time.range([0, width]);

                    
                    scale.time.domain([$ctrl.startTime.toDate(), $ctrl.endTime.toDate()]);

                    var svg = d3.select($svg[0]);


                    _(lines).each(function (lineFunction, lineName) {
                            svg.append('path')
                                .datum(data)
                                .attr('class', 'line ' + lineName)
                                .attr('d', lineFunction);
                        });



                }

                //  Rerender the line chart
                function rerenderChart(data, $svg) {
                    
                    var svg = d3.select($svg[0]);

                    scale.time.domain([$ctrl.startTime.toDate(), $ctrl.endTime.toDate()]);

                    var translate = scale.time($ctrl.endTime) - scale.time($ctrl.lastEndTime);

                    _(lines).each(function (lineFunction, lineName) {
                        svg.selectAll('path.' + lineName)
                                .data([data])
                                .attr("transform", "translate(" + translate + ")")
                                .attr('d', lineFunction)
                                .transition()
                                .duration($ctrl.refreshInterval / 2)
                            .attr("transform", "translate(0)");
                        });

                }


                $ctrl.init();

                //$interval($ctrl.refresh, 500);

            }]



        };


    });

})();