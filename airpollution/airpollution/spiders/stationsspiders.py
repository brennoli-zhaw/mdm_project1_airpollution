import scrapy
import json

class StationsSpider(scrapy.Spider):
    name = "stations"
    allowed_domains = ["aqicn.org", "airnet.waqi.info", "api2.waqi.info"]
    start_urls = ['https://aqicn.org/map/switzerland/de/']

    def parse(self, response):
        try:
            countryHrefs = response.css('.country-list a::attr("href")').getall()
            for countryHref in countryHrefs:
                countryLink = "https://aqicn.org" + countryHref
                yield response.follow(countryLink, callback=self.parse_stations)
        except:
            self.logger.error("Something went wrong")

    def parse_stations(self, response):
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
                        yield response.follow(newLink, callback=self.getGeoByAPITypeOne, cb_kwargs={'data' : data}) 
                else:
                    #type two needs some more scaping to get the station ID first than requests to a url in following structure https://api2.waqi.info/api/feed/{@stationId}/aqi.json
                    #yield response.follow(link, callback=self.getGeoByAPITypeTwo, cb_kwargs={'data' : data})
                    yield response.follow(link, callback=self.getGeoDataByInlineScript, cb_kwargs={'data' : data})
                    
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
                'lat' : float(jsonresponse['meta']['geo'][0]),
                'lng' : float(jsonresponse['meta']['geo'][1])
            }
            yield data
        except:
            self.logger.error("Error with Json structure:  type one " + response.text)
            data['geo'] = 'error : json structure type one'
            yield data
       

    def getGeoByAPITypeTwo(self, response, data=None):
        link = response.css("a#iosurl").attrib['href']
        if(link.find('?') == -1):
            self.logger.error("Error with Json structure: type two " + link)
            data['geo'] = 'error : type two ' + link
            yield data
        else:
            idPart = link.split('?')
            stationID = idPart[1]
            newLink = "https://api2.waqi.info/api/feed/@" + stationID + "/aqi.json"
            data['data-point'] = newLink
            #headers are needed, otherwise only parts of the json file will be responded
            customHeaders = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
                'Cache-Control': 'no-cache',
                'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
                'Sec-Ch-Ua-Platform': '"Windows"',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                
                
            }
            yield response.follow(newLink, self.getGeoDataByApiFeed, cb_kwargs={'data':data})
    #deprecated, this endpoint doesn't repsond enough information anymore
    def getGeoDataByApiFeed(self, response, data=None):
        try:
            jsonresponse = json.loads(response.text)
            geo = jsonresponse['rxs']['obs'][0]['msg']['city']['geo']
            data['geo'] = {
                'lat' : float(geo[0]),
                'lng' : float(geo[1])
            }
            yield data
        except:
            self.logger.error("Error with Json structure: type two " + response.text)
            #try getting data from js
            yield response.follow(data["link"], self.getGeoDataByInlineScript, cb_kwargs={'data':data})

    def getGeoDataByInlineScript(self, response, data=None):
        try:
            if response.css("div#citydivouter") is not None:
                scriptText = response.css("div#citydivouter script::text").get()
                sciptSplitter = scriptText.split("try { setWidgetAqiGraphModel(")
                sciptSplitter = sciptSplitter[1].split("); } catch(e) { }")
                jsonpart = json.loads(sciptSplitter[0])
                geo = jsonpart["city"]["geo"]
                data['geo'] = {
                    'lat' : float(geo[0]),
                    'lng' : float(geo[1])
                }
                yield data
        except:
            data["geo"] = "error: we tried everything"
            yield data
        
    
        