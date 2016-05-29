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

                $ctrl.refresh = function() {
                    $http.get('/sense/current').then(function(data) {
                        $ctrl.current = data.data;
                    });
                }

                $ctrl.transformPitch = function(orientation) {

                    var pitch = 360 - orientation.pitch;
                    if (orientation.roll <= 90 || orientation.roll >= 270) {
                        pitch = pitch;
                    }
                    if (orientation.roll > 90 && orientation.roll < 270) {
                        pitch = 180 - pitch;
                    }
                    return pitch;

                }

                $interval($ctrl.refresh, 500);
            }]
        };
    });

})();