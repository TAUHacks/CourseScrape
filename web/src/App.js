import './App.css';
import myData from "./out.json";
import {useState} from 'react';

const days = ["א", "ב", "ג", "ד", "ה", "ו"];

function App() {
  const [myMyData, setMyMyData] = useState(() => {
    for (let i = 0; i < myData.length; i++) {
      myData[i]["checked"] = false;
    }
    const res = myData.filter(x => (x["lessons"].filter(y => y["time"] !== "").length > 0));
    res.sort((x, y) => x["name"] < y["name"])
    return res;
  });

  // find all checked stuff, put in calendar
  const checkedStuff = myMyData.filter(x => x["checked"]);
  return (
    <div>
      <h1>Hello world!</h1>
      <table dir="rtl" width="100%">
        <thead>
          <tr>
            <th width="1px">שעה</th>
            {days.map(x => <th key={"headThing" + x}>{x}</th>)}
          </tr>
        </thead>
        <tbody>
          { [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21].map(hour => {
              const forAllDays = days.map(d => []);
              for (let thing of checkedStuff) {
                for (let lesson of thing["lessons"]) {
                  if (lesson["time"].length > 1 && lesson["time"].split("-")[0].split(":")[0] <= hour && lesson["time"].split("-")[1].split(":")[0] > hour) {
                    forAllDays[days.indexOf(lesson["day"])].push(thing["name"] + " ב-" + lesson["time"]);
                  }
                }
              }
              console.log(days);
              return (
                <tr key={"h" + hour}>
                  <td>{hour}:00-{hour + 1}:00</td>
                  { days.map((day, i) => 
                    (<td key={"abjasdjasfjag" + day + "h" + hour}>
                      {forAllDays[i].toString()}
                    </td>)
                  ) }
                </tr>
              );
          }) }
        </tbody>
      </table>
      <table dir="rtl" width="100%">
        <thead>
          <tr>
            <th>✅</th>
            <th>פקולטה</th>
            <th>קורס</th>
            <th>מרצה</th>
            <th>קבוצה</th>
            <th>שעות</th>
          </tr>
        </thead>
        <tbody>
          {
            myMyData.map((x, i) => 
              (<tr key={i}>
                <td><input key={"in" + i} onChange={ev => {
                  const xClone = myMyData.map(x => { return { ...x } });
                  xClone[i]["checked"] = ev.target.checked;
                  setMyMyData(xClone);
                }} checked={x["checked"]} type="checkbox" /></td>
                <td>{x["faculty"]}</td>
                <td>{x["name"]}</td>
                <td>{x["lecturer"]}</td>
                <td>{x["group"]}</td>
                <td>{x["lessons"].filter(y => y["time"] !== "").map(y => y["time"] + " יום " + y["day"] + " סמסטר " + y["semester"]).toString()}</td>
              </tr>)
            )
          }
        </tbody>
      </table>
    </div>
  );
}

export default App;
