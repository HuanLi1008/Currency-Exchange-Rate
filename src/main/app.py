#!/usr/bin/env python3

from flask import Flask, request, render_template, flash, redirect, url_for
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from src.main.data_collector import collect_data
from src.main.data_analyzer import data_analyzer
import pika, os
def create_app():
    app = Flask(__name__)

    supported_currencies = {"AUD":"Australian Dollar","BGN":"Bulgarian Lev","BRL":"Brazilian Real","CAD":"Canadian Dollar","CHF":"Swiss Franc","CNY":"Chinese Renminbi Yuan","CZK":"Czech Koruna","DKK":"Danish Krone","EUR":"Euro","GBP":"British Pound","HKD":"Hong Kong Dollar","HUF":"Hungarian Forint","IDR":"Indonesian Rupiah","ILS":"Israeli New Sheqel","INR":"Indian Rupee","ISK":"Icelandic Króna","JPY":"Japanese Yen","KRW":"South Korean Won","MXN":"Mexican Peso","MYR":"Malaysian Ringgit","NOK":"Norwegian Krone","NZD":"New Zealand Dollar","PHP":"Philippine Peso","PLN":"Polish Złoty","RON":"Romanian Leu","SEK":"Swedish Krona","SGD":"Singapore Dollar","THB":"Thai Baht","TRY":"Turkish Lira","USD":"United States Dollar","ZAR":"South African Rand"}

    @app.route("/")
    def main():
        return render_template('index.html', currencies=supported_currencies)
        

    @app.route("/submit", methods=["POST"])
    def line_chart():
        base = request.form.get('currency-from')
        target = request.form.get('currency-to')
        period = int(request.form.get('period'))

        if base == target:
            return redirect(url_for("main"))
        collect_data(base, target, period)
        result = data_analyzer(base, target, period)
        
        x = result["dates"]
        y = result["rates"]

        # Create a dynamic line chart using Plotly
        fig = make_subplots(rows=1, cols=1)
        fig.add_trace(go.Scatter(x=x, y=y, mode='lines', name='Line Chart'))

        # Customize the chart layout 
        fig.update_layout(
            title_text='Exchange Rate From %s To %s' %(supported_currencies[base], supported_currencies[target]),
            title_x=0.5,
            title=dict(font=dict(family="Helvetica", size=20)),
            xaxis_title='Date',
            yaxis_title='Exchange-Rate'
        )
        

        # Convert the Plotly chart to JSON
        chart_json = fig.to_json()

        return render_template('line_chart.html', currencies=supported_currencies, chart_json=chart_json, a=result["min"], b=result["max"], c=result["average"])
        

    if __name__ == "__main__":
        app.run(debug=True)
    return app
create_app()

def publish(base, target, period):
    url = os.environ.get('CLOUDAMQP_URL')
    params = pika.URLParameters(url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel() # start a channel
    channel.queue_declare(queue='collect_data') # Declare a queue
    channel.basic_publish(exchange='',
                        routing_key='1',
                        body= base + target + period)
    print("message send")
    connection.close()