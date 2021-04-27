from urllib.request import urlopen as uReq
import requests
from logger_class import getLog
from bs4 import BeautifulSoup as bs
from flask import Flask, render_template, request
from flask_cors import CORS, cross_origin

from requests import get

import threading

import pymongo
import plotly as py
import plotly.graph_objects as go
import json
import pandas as pd

logger = getLog("flipkart.py")

def saveDataFrameToFile(dataframe, file_name):
    """
        This function saves dataframe into filename given
    """
    try:
        data = pd.DataFrame(dataframe)
        data.to_csv(file_name)
    except Exception as e:
        print(e)


def product_details(product_page, productLink, searchstring):
    """
     This function collects the details of products
    """
    product_detail = []
    try:
        product_image_url = product_page.find_all('div', {'class': 'q6DClP'})[0].attrs['style']
        product_image_url = product_image_url[product_image_url.find('(') + 1:-1].replace('128', '352')
        # print(product_image_url)

    except:
        product_image_url = 'No image availbel for ' + searchstring
    try:
        product_name = product_page.find_all("span", {"class": "B_NuCI"})[0].text
        product_name = product_name[:product_name.find("(")]
        # print(product_name)
    except:
        product_name = "samsung"
    try:
        product_price = product_page.find_all('div', {"class": '_30jeq3 _16Jk6d'})[0].text
        # print(product_price)
    except:
        product_price = 'Not available'
    try:
        actual_price = product_page.find_all("div", {"class": "_3I9_wc _2p6lqe"})[0].text
        # print(actual_price)
    except:
        actual_price = "Price Not available"
    try:
        discount = product_page.find_all("div", {"class", "_3Ay6Sb _31Dcoz"})[0].text
        # print(discount)
    except:
        discount = "No Discount"
    try:
        offers = product_page.find_all("div", {"class": "WT_FyS"})[0].text
        # print(offers)
    except:
        offers = "No offers available"
    try:
        payment_methods = product_page.find_all("div", {"class": "_3vDXYV flex"})[0].text
        # print(payment_methods)
    except:
        payment_methods = "Not available"

    dct = {"Product Image Url": product_image_url, "Product Link": productLink, "Product Name": product_name,
           "Price": product_price,
           "MRP": actual_price, "Discount": discount, "Offers": offers, "Payment Methods": payment_methods}
    product_detail.append(dct)
    return product_detail


def get_pie_chart():
    """
        This function returns pie chart of review ratings
    """
    filename = "static/CSVs" + searchstring + ".csv"
    review_data = pd.read_csv(filename)
    starts = pd.Series([1, 2, 3, 4, 5])
    rating = review_data["Rating"]
    data = go.Figure(data=[go.Pie(labels=rating, values=starts,
                                  hole=.4, hoverinfo='label+value', title='User Rating')])
    graphJSON = json.dumps(data, cls=py.utils.PlotlyJSONEncoder)
    return graphJSON


def get_scatter_plot():
    """
    This function returns scatter plot for likes and dislikes
    """
    filename = "static/CSVs" + searchstring + ".csv"
    review_data = pd.read_csv(filename)
    data = go.Figure(data=[go.Scatter(x=review_data["Likes"], y=review_data["Dislikes"],
                                      mode="markers",
                                      marker_color='rgba(199, 10, 165, .9)',
                                      marker_size=10)])

    graphJSON = json.dumps(data, cls=py.utils.PlotlyJSONEncoder)
    return graphJSON


def getrequiredreviews(prod_html, searchstring, required_reviews,review_count):
    """To get the next link"""

    try:
        next_link = prod_html.find("div", {"class": "_3UAT2v _16PBlm"})
        next_link = next_link.find_parent().attrs['href']
        next_review_link = "https://www.flipkart.com" + next_link
        logger.info("Next link hitted")
        next_review_page = requests.get(next_review_link)
        next_page_html = bs(next_review_page.text, 'html.parser')
        mx = next_page_html.find_all('div', {'class': '_2MImiq _1Qnn1K'})[0].text
        max_reviews_pages = mx[mx.find('of') + 2:]
        max_reviews_pages = max_reviews_pages.replace(',', '')
        max_reviews_pages = int(max_reviews_pages[:3])

    except:
        print("Error in response")
    pages = [str(i) for i in range(1, max_reviews_pages)]
    req = 0
    details = []
    #start_time = time()
    total_reviews = int(
        prod_html.find_all('div', {'class': "_3UAT2v _16PBlm"})[0].text.replace('All', '').replace('reviews', ''))

    """ Scrapping required numbers of reviews"""

    """ Iterating throuhg requiured number of pages """
    for page in pages:
        if len(details) == required_reviews:
            break
            logger.info("Scrap completed")
        else:
            """To get the next link"""
            try:
                response = get(next_review_link + page)
            except:
                logger.info("NO next link found")

            " Controlling the request "
            try:
                req += 1
                if req > (required_reviews / 10):
                    logger.info("'Number of requests was greater than expected.'")
                    logger.info('Number of requests was greater than expected.')

                temp_review_page_html = bs(response.text, 'html.parser')
                bx = temp_review_page_html.find_all('div', {'class': '_1AtVbE col-12-12'})
                del bx[0:1]
                cmt = temp_review_page_html.find_all('div', {'class': "_27M-vq"})
            except:
                print("Error in box")

            """ Srapping the data from pages one by one """
            try:
                product_name = prod_html.find_all('span', {'class': "B_NuCI"})[0].text
                product_name = product_name[:product_name.find('(')]
                # print(product_name)
            except:
                product_name = searchstring
            #review_count = len(reviews)
            for b in cmt:
                if review_count == required_reviews:
                    break
                else:
                    try:
                        name = b.div.div.find_all('p', {'class': '_2sc7ZR _2V5EHH'})[0].text
                    except:
                        name = 'No Name'
                    try:
                        rating = b.div.div.div.div.text
                    except:
                        rating = 'No Rating'
                    try:
                        commentHead = b.div.div.div.p.text
                    except:
                        commentHead = 'No Comment Heading'
                    try:
                        comtag = b.div.div.find_all('div', {'class': ''})
                        custComment = comtag[0].div.text
                    except:
                        custComment = "No Customer Comment"
                    try:
                        verification = b.find_all("p", {"class": "_2mcZGG"})[0].text
                    except:
                        verification = "Not certified"
                    try:
                        review_period = b.find_all("p", {"class": "_2sc7ZR"})[1].text
                    except:
                        review_period = "Not mentioned"
                    try:
                        likes = b.find_all("span", {"class": "_3c3Px5"})[0].text
                    except:
                        likes = "0"
                    try:
                        dislikes = b.find_all("span", {"class": "_3c3Px5"})[1].text
                    except:
                        dislikes = "0"

                    mydict = dict(Product=product_name, Name=name, Rating=rating, CommentHead=commentHead,
                                  Comment=custComment, Customer=verification, Period=review_period, Likes=likes,
                                  Dislikes=dislikes)

                    details.append(mydict)
                    review_count = review_count + 1

    return details

free_status = True
collection_name = None

app = Flask(__name__)


#To avoid the time out issue on heroku
class threadClass:

    def __init__(self,prod_html, searchstring, required_reviews,review_count):
        self.prod_html= prod_html
        self.searchstring = searchstring
        self.required_reviews = required_reviews
        self.review_count = review_count
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True  # Daemonize thread
        thread.start()  # Start the execution

    def run(self):
        global collection_name, free_status
        free_status = False
        self.collection_name = getrequiredreviews( prod_html=self. prod_html,searchstring=self.searchstring,
                                              required_reviews=self.required_reviews,
                                              review_count=self.review_count)

        logger.info("Thread run completed")
        free_status = True

@app.route("/", methods=["POST", "GET"])
@cross_origin()
def index():
    if request.method == "POST":
        global searchstring
        global  free_status
        ## To maintain the internal server issue on heroku
        if free_status != True:
            return "This website is executing some process. Kindly try after some time..."
        else:
            free_status = True

        searchstring = request.form['content'].replace("", "")
        required_reviews = int(request.form['expected_review'])

        flipkart_url = "https://www.flipkart.com/search?q=" + searchstring
        logger.info(f"Search begins for {searchstring}")
        uClient = uReq(flipkart_url)
        flipkartpage = uClient.read()
        uClient.close()
        flipkart_html = bs(flipkartpage, "html.parser")
        boxes = flipkart_html.findAll("div", {"class": "_1AtVbE col-12-12"})
        del boxes[0:3]
        box = boxes[5]
        productLink = "https://www.flipkart.com" + box.div.div.div.a['href']
        prodRes = requests.get(productLink)
        prod_html = bs(prodRes.text, "html.parser")
        logger.info("Url hitted")
        commentates = prod_html.find_all('div', {'class': "_16PBlm"})


        """ connecting with database"""
        try:
            dbConn = pymongo.MongoClient("mongodb://localhost:27017/")  # opening a connection to Mongo
            db = dbConn['new_scrapper']  # connecting to the database called crawlerDB
            logger.info("Database created")
            reviews = db[searchstring].find({})  # searching the collection with the name same as the keyword
            if len(reviews)> required_reviews:
                reviews = [reviews[i] for i in range(0, required_reviews)]
                return render_template('results.html', reviews=reviews)  # show the results to user
            else:
                reviews=[]
                review_count=len(reviews)
                reviews = getrequiredreviews(prod_html, searchstring, required_reviews, review_count)
                logger.info("Reviews Collected")
                table = db[searchstring]  # creating a collection with the same name as search string. Tables and Collections are analogous.
                x = table.insert_many(reviews)

                filename = "static/CSVs" + searchstring + ".csv"  # filename to save the details
                saveDataFrameToFile(dataframe=reviews, file_name=filename)
                logger.info(f"New file {filename} created")


                threadClass(prod_html=prod_html,required_reviews=required_reviews,searchstring=searchstring,review_count=review_count)


                try:
                    total_reviews = int(prod_html.find_all('div', {'class': "_3UAT2v _16PBlm"})[0].text.replace('All', '').replace('reviews', ''))
                    if total_reviews < required_reviews:
                        return "<h4>Enter valid number of Reviews</h4>"

                    elif len(reviews) > required_reviews:

                        reviews = [reviews[j] for j in range(0, required_reviews)]
                        x = table.insert_many(reviews)
                        logger.info(f"Required reviews {required_reviews} scrapped")

                        saveDataFrameToFile(dataframe=reviews, file_name=filename)
                        logger.info("Data saved")
                        threadClass(prod_html=prod_html, required_reviews=required_reviews, searchstring=searchstring,
                                    review_count=review_count)
                        return render_template("results.html", reviews=reviews)

                    else:
                        threadClass(prod_html=prod_html, required_reviews=required_reviews, searchstring=searchstring,
                                    review_count=review_count)
                        return render_template("results.html", reviews=reviews)


                except Exception as e:
                    print(e)
                    return "<h4> try after some time</h4>"


                return render_template("results.html", reviews=reviews)

                x = table.insert_many(reviews)

                saveDataFrameToFile(dataframe=details, file_name=filename)


        except:
            return render_template("error.html")
    else:
        return render_template("index.html")


@app.route("/detail", methods=["POST", "GET"])
@cross_origin()
def detail():
    try:
        products = []
        product_highlights = []
        flipkart_url = "https://www.flipkart.com/search?q=" + searchstring
        uClient = uReq(flipkart_url)
        flipkartpage = uClient.read()
        uClient.close()
        flipkart_html = bs(flipkartpage, "html.parser")
        boxes = flipkart_html.findAll("div", {"class": "_1AtVbE col-12-12"})
        del boxes[0:3]
        box = boxes[0]
        productLink = "https://www.flipkart.com" + box.div.div.div.a['href']
        prodRes = requests.get(productLink)
        prod_html = bs(prodRes.text, "html.parser")
        product_deatil = product_details(prod_html, productLink, searchstring)
        products.extend(product_deatil)

        return render_template("details.html", prod_details=products)

    except Exception as e:
        print(e)


@app.route("/Dashboard", methods=["GET", "POST"])
@cross_origin()
def Dashboard():
    try:
        bar = get_pie_chart()
        logger.info("Bar graph created")
        Scatter = get_scatter_plot()
        logger.info("Scatter plot created")
        return render_template("Dashboard.html", plot=bar, Scatter=Scatter)

    except Exception as e:
        print(e)

if __name__ == "__main__":
    app.run()

