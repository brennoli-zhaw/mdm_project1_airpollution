import scrapy
import json

class StationsSpider(scrapy.Spider):
    name = "stations"
    allowed_domains = ["aqicn.org", "airnet.waqi.info", "api2.waqi.info"]
    start_urls = ['https://aqicn.org/map/switzerland/de/']

    def parse(self, response):
        stations = response.css('#map-station-list>div')
        for station in stations:
            try:
                link = station.css('a').attrib['href']
                hasStation = '@' in link
                data = {
                    'place': station.css('a::text').get(),
                    'link': link,
                    'current-score': station.css('a > div::text').get(),
                }
                if hasStation:
                    #type one sends a request directly to an API using following stucture https://airnet.waqi.info/airnet/feed/instant/{stationId}
                    linkParts = link.split("@")
                    if(link.find('@') == -1):
                        data['geo'] = 'error : type one ' + link
                        yield data
                    else:
                        idPart = linkParts[1].split("/")
                        stationID = idPart[0]
                        newLink = "https://airnet.waqi.info/airnet/feed/instant/" + stationID
                        data['data-point'] = newLink
                        #yield {
                        #    'json' : response.follow(newLink, self.getGeoByAPITypeOne)
                        #}
                        yield response.follow(newLink, callback=self.getGeoByAPITypeOne, cb_kwargs={'data' : data}) 
                else:
                    #type two needs some more scaping to get the station ID first than requests to a url in following structure https://api2.waqi.info/api/feed/{@stationId}/aqi.json
                    yield response.follow(link, callback=self.getGeoByAPITypeTwo, cb_kwargs={'data' : data})

            except:
                link = station.css('a').attrib['href']
                yield {
                    'place': station.css('a::text').get(),
                    'link': link,
                    'current-score': station.css('a > div::text').get(),
                    'geo': 'error'
                }

    def getGeoByAPITypeOne(self, response, data=None):
        try:
            jsonresponse = json.loads(response.text)
            data['geo'] = {
                'lat' : jsonresponse['meta']['geo'][0],
                'lng' : jsonresponse['meta']['geo'][1]
            }
            yield data
        except:
            self.logger.error("Error with Json structure:  type one " + response.text)
            data['geo'] = 'error : json structure type one'
            yield data
       

    def getGeoByAPITypeTwo(self, response, data=None):
        link = response.css("a#iosurl").attrib['href']
        self.logger.warning(link)
        if(link.find('?') == -1):
            self.logger.warning(link)
            data['geo'] = 'error : type two ' + link
            yield data
        else:
            idPart = link.split('?')
            stationID = idPart[1]
            newLink = "https://api2.waqi.info/api/feed/@" + stationID + "/aqi.json"
            data['data-point'] = newLink
            #headers are needed, otherwise only parts of the json file will be responded
            customHeaders = {
                "Sec-Ch-Ua-Platform": "\"Linux\"",
                "User-Agent": "Mozilla/5.0 (Linux; x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            }
            yield response.follow(newLink, self.getGeoDataByApiFeed, cb_kwargs={'data':data}, headers=customHeaders)

    def getGeoDataByApiFeed(self, response, data=None):
        try:
            jsonresponse = json.loads(response.text)
            geo = jsonresponse['rxs']['obs'][0]['msg']['city']['geo']
            data['geo'] = {
                'lat' : geo[0],
                'lng' : geo[1]
            }
            yield data
        except:
            self.logger.error("Error with Json structure: type two " + response.text)
            data['geo'] = 'error : json structure'
            yield data
        
    
        