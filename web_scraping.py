from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium import webdriver
from tabulate import tabulate
import pandas as pd
import time

PATH = "C:\Program Files (x86)\chromedriver.exe"

class HSW_Scraper():
    def __init__(self):
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(executable_path=PATH,options=self.chrome_options)

        self.characters = self.pull_accounts()

    #used to make all images load
    def slow_scroll(self,page_length):
        current = 0
        while current <= page_length - 21:
            self.driver.execute_script(f"window.scrollTo({current}, {current + 20});")
            current += 19
    
    #used once at launch because very innefficient
    def pull_accounts(self):
        hsw_url = 'https://housestockwatcher.com/summary_by_rep'
        self.driver.get(hsw_url)
        time.sleep(4)
        self.slow_scroll(self.driver.execute_script("return document.body.scrollHeight"))
        characters = {}
        # populates dict with name, image, and role in house from site
        for x,profile in enumerate(self.driver.find_elements(By.XPATH,'/html/body/div[1]/div/div/div/div[3]/div/div'),1):
            name = self.driver.find_element(By.XPATH,f'/html/body/div[1]/div/div/div/div[3]/div/div[{x}]/div/h2').text
            try:
                image = self.driver.find_element(By.XPATH,f'/html/body/div[1]/div/div/div/div[3]/div/div[{x}]/div/div/span/img').get_attribute("src")
            except:
                image = None
            role = self.driver.find_element(By.XPATH,f'/html/body/div[1]/div/div/div/div[3]/div/div[{x}]/div/span[1]').text
            characters[name] = {
                'name':name,
                'image':image,
                'role':role
            }
        return characters

    # innefficient but now we dont have to have the exact name
    def search_characters(self,name):
        if name in self.characters:
            return [self.characters[name]]
        result = []
        for people in self.characters:
            if name.lower() in people.lower() or name.lower() == people.lower():
                result.append(self.characters[people])
        return result

    # searches database for info regarding trades
    def house_watcher(self,name, size):
        # save name for readability
        intact = str(name)
        print(intact)
        name = intact.split(' ')
        #assemble URL from name
        url_name = name[0]
        for x in range(1,len(name)):
            url_name += '%20'+ name[x]
        hsw_url = f'https://housestockwatcher.com/summary_by_rep/{url_name}'
        print(hsw_url)

        # get data from site
        self.driver.get(hsw_url)
        # site takes time to boot
        time.sleep(3)
        table1 = self.driver.find_elements(By.TAG_NAME,'table')[1]
        
        # get table info
        table_rows = []
        for i in table1.find_elements(By.TAG_NAME,'tr')[1:]:
            raw_text = i.text
            row = raw_text.split('\n')
            row[-1] = row[-1][:-5]
            table_rows.append(row)
        
        # assemble table
        df = pd.DataFrame(data=table_rows,columns=['DATE','TICKER','TYPE','AMOUNT'])
        results = ''
        if size <= 25:
            results = f'```{str(tabulate(df[:size],["DATE","TICKER","TYPE","AMOUNT"],tablefmt="orgtbl",))}```'
        else:
            results = f'```{df[:size]}```'
        return [results, self.characters[intact]]

class Market_Watcher_Scraper():
    def __init__(self):
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")
        self.driver = webdriver.Chrome(executable_path=PATH,options=self.chrome_options)
        self.mw_url = 'https://www.marketwatch.com/investing/stock/{}/analystestimates'

    def get_price(self,ticker):
        self.driver.get(self.mw_url.format(ticker))
        price = float(self.driver.find_element(By.XPATH,'/html/body/div[3]/div[1]/div[3]/div/div[2]/h2/bg-quote').text)
        return price

    def get_recommendation(self,ticker):
        self.driver.get(self.mw_url.format(ticker))
        data = self.driver.find_element(By.XPATH,'/html/body/div[3]/div[6]/div[1]/div[1]/div/table/tbody/tr[1]/td[2]').text
        return data

if __name__ == '__main__':
    mws = Market_Watcher_Scraper()
    print(mws.get_recommendation('nvda'))
    print(mws.get_price('NVDA'))