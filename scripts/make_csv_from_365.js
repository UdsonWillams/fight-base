(function() {
  const fighterNameElements = document.querySelectorAll('.src-ParticipantFixtureDetailsHigher_TeamAndScoresContainer .src-ParticipantFixtureDetailsHigher_TeamNames');
  const oddsElements = document.querySelectorAll('.cm-CouponMarketGrid.gl-MarketGrid .src-ParticipantOddsOnly50_Odds');

  const fighterNames = Array.from(fighterNameElements).map(el => el.textContent.trim());
  const odds = Array.from(oddsElements).map(el => el.textContent.trim());

  let fightData = [];
  let oddsIndex = 0;

  for (let i = 0; i < fighterNames.length; i++) {
    // This regex splits concatenated names, assuming names start with a capital letter
    const names = fighterNames[i].match(/[A-Z][a-z]+(?:\s[A-Z][a-z]+)*/g); 
    if (names && names.length >= 2) {
      const fighter1 = names[0];
      const fighter2 = names[1];

      let odds1 = null;
      let odds2 = null;

      if (oddsIndex < odds.length) {
        odds1 = odds[oddsIndex];
        oddsIndex++;
      }
      if (oddsIndex < odds.length) {
        odds2 = odds[oddsIndex];
        oddsIndex++;
      }
      fightData.push({ fighter1: fighter1, odds1: odds1, fighter2: fighter2, odds2: odds2 });
    } else if (names && names.length === 1) {
      const fighter1 = names[0];
      let odds1 = null;
      if (oddsIndex < odds.length) {
        odds1 = odds[oddsIndex];
        oddsIndex++;
      }
      fightData.push({ fighter1: fighter1, odds1: odds1, fighter2: null, odds2: null });
    } else {
      fightData.push({ fighter1: fighterNames[i], odds1: null, fighter2: null, odds2: null });
    }
  }

  let csvContent = "Fighter 1,Odds 1,Fighter 2,Odds 2\n";
  fightData.forEach(row => {
    csvContent += `"${row.fighter1 || ''}","${row.odds1 || ''}","${row.fighter2 || ''}","${row.odds2 || ''}"\n`;
  });

  console.log(csvContent);

  // You can also automatically download it as a CSV file:
  // const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  // const link = document.createElement('a');
  // if (link.download !== undefined) {
  //   const url = URL.createObjectURL(blob);
  //   link.setAttribute('href', url);
  //   link.setAttribute('download', 'fighter_odds.csv');
  //   link.style.visibility = 'hidden';
  //   document.body.appendChild(link);
  //   link.click();
  //   document.body.removeChild(link);
  // }
})();