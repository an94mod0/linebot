# 2019/5/26 16:00 commit by an94mod0

##更新內容
* 完成時間輸入(使用postback)，禁止輸入過去時間
* 完成查看歷史訂單功能

## TODO
* 電話未做防呆
* 有orderID後刪除可以做成button形式

# 2019/5/26 13:00 commit by an94mod0
## 更新內容
* 清理無用程式碼
* 大幅修改程式架構
* 使用class取代原本的local varible避免多個line使用者間發生衝突
* 每當有新的(未登記)使用者發訊息時根據建立一個User類別 `CurrentUser=User(lineID)`
* `CurrentUser.action`決定外層架構(下訂單,修改,刪除)
* 優化下單填資料的過程，把使用者輸入放進button以便查看


## TODO
* 時間輸入還沒有處理(考慮使用postback)
* 修改與刪除部分都還沒做
* 地址?備註欄?
* 考慮在資料庫新增一個orderID的column做主鍊
* action的判斷仍有bug