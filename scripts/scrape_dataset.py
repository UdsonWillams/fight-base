import os
import asyncio
import warnings

import httpx
import pandas as pd
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

warnings.filterwarnings("ignore", category=RuntimeWarning)

# Ensure the datasets directory exists
os.makedirs("datasets", exist_ok=True)

fight_details = []
new_fight_links_all = []
winner_names = []
fighter_detail_data = []

MAX_CONCURRENT_REQUESTS = 5  # adjust to change concurrency

ua = UserAgent()
chrome = getattr(
    ua,
    "chrome",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
)

HEADER = {"User-Agent": chrome}


async def fetch_html(client, url):
    """Fetch HTML from a URL with async retry logic."""
    for attempt in range(5):
        try:
            response = await client.get(url, headers=HEADER, timeout=15.0)
            response.raise_for_status()
            return response.text
        except Exception as e:
            if attempt == 4:
                print(f"Failed to fetch {url}: {e}")
                return None
            await asyncio.sleep(2**attempt)  # Exponential backoff


async def get_event_data(client, semaphore, idx, link):
    """Scrape event data from the given link."""
    link = link.strip()
    async with semaphore:
        html = await fetch_html(client, link)
        if not html:
            return

        soup = BeautifulSoup(html, "lxml")
        event_id = link[-16:]
        date_loc_list = soup.find_all("li", "b-list__box-list-item")
        if len(date_loc_list) >= 2:
            date = date_loc_list[0].text.replace("Date:", "").strip()
            location = date_loc_list[1].text.replace("Location:", "").strip()
        else:
            date = None
            location = None

        fight_links = soup.find_all(
            "tr",
            class_="b-fight-details__table-row b-fight-details__table-row__hover js-fight-details-click",
        )
        for i in fight_links:
            winner_name = None
            winner_id = None
            w_l_d_tag = i.find("i", class_="b-flag__text")
            w_l_d = w_l_d_tag.text if w_l_d_tag else None

            data_link = i.get("data-link")
            if not data_link:
                continue

            fight_id = data_link[-16:]
            if w_l_d == "win":
                players = i.find(
                    "td", class_="b-fight-details__table-col l-page_align_left"
                )
                if players:
                    players_list = players.find_all(
                        "a", class_="b-link b-link_style_black"
                    )
                    if players_list:
                        winner_name = players_list[0].text.strip()
                        winner_id = players_list[0]["href"][-16:]

            data_dic = {
                "event_id": event_id,
                "fight_id": fight_id,
                "date": date,
                "location": location,
                "winner": winner_name,
                "winner_id": winner_id,
            }
            new_fight_links_all.append(data_link)
            winner_names.append(data_dic)


async def get_fight_data(client, semaphore, idx, link):
    """Scrape fight data from the given link."""
    link = link.strip()
    async with semaphore:
        html = await fetch_html(client, link)
        if not html:
            return

        soup = BeautifulSoup(html, "lxml")

        event_link_tag = soup.find("a", class_="b-link")
        if not event_link_tag:
            return
        event_name = event_link_tag.text.strip()
        event_id = event_link_tag["href"][-16:]
        fight_id = link[-16:]

        fighter_nams = soup.find_all("a", class_="b-link b-fight-details__person-link")
        if len(fighter_nams) < 2:
            return
        r_name = fighter_nams[0].text.strip()
        b_name = fighter_nams[1].text.strip()

        r_id = fighter_nams[0]["href"].strip()[-16:]
        b_id = fighter_nams[1]["href"].strip()[-16:]

        division_tag = soup.find("i", class_="b-fight-details__fight-title")
        division_info = division_tag.text.lower() if division_tag else ""
        is_title_fight = 1 if "title" in division_info else 0
        division_info = (
            division_info.replace("ufc", "")
            .replace("title", "")
            .replace("bout", "")
            .strip()
        )

        method_tag = soup.find("i", style="font-style: normal")
        method = method_tag.text.strip() if method_tag else None

        p_tag_with_fight_detail = soup.find("p", class_="b-fight-details__text")
        if p_tag_with_fight_detail:
            fight_details_list = p_tag_with_fight_detail.find_all(
                "i", class_="b-fight-details__text-item"
            )
            if len(fight_details_list) >= 4:
                finish_round_str = (
                    fight_details_list[0].text.lower().replace("round:", "").strip()
                )
                finish_round = (
                    int(finish_round_str) if finish_round_str.isdigit() else None
                )

                match_timestamp = (
                    fight_details_list[1].text.lower().replace("time:", "").strip()
                )
                match_timestamp_splited = match_timestamp.split(":")
                if len(match_timestamp_splited) == 2:
                    match_time_sec = int(match_timestamp_splited[0]) * 60 + int(
                        match_timestamp_splited[-1]
                    )
                else:
                    match_time_sec = None

                total_rounds_str = (
                    fight_details_list[2]
                    .text.lower()
                    .replace("time format:", "")
                    .strip()
                )
                if total_rounds_str == "no time limit":
                    total_rounds = None
                else:
                    total_rounds = (
                        int(total_rounds_str[0]) if total_rounds_str else None
                    )

                referee = fight_details_list[3].text.replace("Referee:", "").strip()
            else:
                finish_round, match_time_sec, total_rounds, referee = (
                    None,
                    None,
                    None,
                    None,
                )
        else:
            finish_round, match_time_sec, total_rounds, referee = None, None, None, None

        # PARSE ADVANCED TABLES
        tables = soup.find_all("table", style="width: 745px")
        if len(tables) > 0:
            table1 = tables[0]
            td_1_list = table1.find_all("td", class_="b-fight-details__table-col")

            kd_players = td_1_list[1].text.split()
            r_kd, b_kd = int(kd_players[0]), int(kd_players[1])

            sig_str_players = td_1_list[2].text.split()
            r_sig_str_landed, r_sig_str_atmpted = (
                int(sig_str_players[0]),
                int(sig_str_players[2]),
            )
            b_sig_str_landed, b_sig_str_atmpted = (
                int(sig_str_players[3]),
                int(sig_str_players[5]),
            )

            sig_str_acc = td_1_list[3].text.split()
            r_sig_str_acc = (
                int(sig_str_acc[0].replace("%", ""))
                if sig_str_acc[0] != "---"
                else None
            )
            b_sig_str_acc = (
                int(sig_str_acc[1].replace("%", ""))
                if sig_str_acc[1] != "---"
                else None
            )

            total_str = td_1_list[4].text.split()
            r_total_str_landed, r_total_str_atmpted = (
                int(total_str[0]),
                int(total_str[2]),
            )
            b_total_str_landed, b_total_str_atmpted = (
                int(total_str[3]),
                int(total_str[5]),
            )

            r_total_str_acc = (
                int(round(r_total_str_landed / r_total_str_atmpted, 2) * 100)
                if r_total_str_atmpted > 0
                else None
            )
            b_total_str_acc = (
                int(round(b_total_str_landed / b_total_str_atmpted, 2) * 100)
                if b_total_str_atmpted > 0
                else None
            )

            td_players = td_1_list[5].text.split()
            r_td_landed, r_td_atmpted = int(td_players[0]), int(td_players[2])
            b_td_landed, b_td_atmpted = int(td_players[3]), int(td_players[5])

            td_acc = td_1_list[6].text.split()
            r_td_acc = int(td_acc[0].replace("%", "")) if td_acc[0] != "---" else None
            b_td_acc = int(td_acc[1].replace("%", "")) if td_acc[1] != "---" else None

            sub_att = td_1_list[7].text.split()
            r_sub_att, b_sub_att = int(sub_att[0]), int(sub_att[1])

            rev = td_1_list[8].text.split()
            r_rev, b_rev = int(rev[0]), int(rev[1])

            ctrl = td_1_list[9].text.split()
            r_ctrl_split = ctrl[0].split(":")
            r_ctrl = (
                int(r_ctrl_split[0]) * 60 + int(r_ctrl_split[1])
                if ctrl[0] != "--"
                else None
            )
            b_ctrl_split = ctrl[1].split(":")
            b_ctrl = (
                int(b_ctrl_split[0]) * 60 + int(b_ctrl_split[1])
                if ctrl[1] != "--"
                else None
            )

            if len(tables) > 1:
                table2 = tables[1]
                td_2_list = table2.find_all("td", class_="b-fight-details__table-col")

                head_list = td_2_list[3].text.split()
                r_head_landed, r_head_atmpted = int(head_list[0]), int(head_list[2])
                b_head_landed, b_head_atmpted = int(head_list[3]), int(head_list[5])
                r_head_acc = (
                    int(round(r_head_landed / r_head_atmpted, 2) * 100)
                    if r_head_atmpted > 0
                    else None
                )
                b_head_acc = (
                    int(round(b_head_landed / b_head_atmpted, 2) * 100)
                    if b_head_atmpted > 0
                    else None
                )

                body_list = td_2_list[4].text.split()
                r_body_landed, r_body_atmpted = int(body_list[0]), int(body_list[2])
                b_body_landed, b_body_atmpted = int(body_list[3]), int(body_list[5])
                r_body_acc = (
                    int(round(r_body_landed / r_body_atmpted, 2) * 100)
                    if r_body_atmpted > 0
                    else None
                )
                b_body_acc = (
                    int(round(b_body_landed / b_body_atmpted, 2) * 100)
                    if b_body_atmpted > 0
                    else None
                )

                leg_list = td_2_list[5].text.split()
                r_leg_landed, r_leg_atmpted = int(leg_list[0]), int(leg_list[2])
                b_leg_landed, b_leg_atmpted = int(leg_list[3]), int(leg_list[5])
                r_leg_acc = (
                    int(round(r_leg_landed / r_leg_atmpted, 2) * 100)
                    if r_leg_atmpted > 0
                    else None
                )
                b_leg_acc = (
                    int(round(b_leg_landed / b_leg_atmpted, 2) * 100)
                    if b_leg_atmpted > 0
                    else None
                )

                dist_list = td_2_list[6].text.split()
                r_dist_landed, r_dist_atmpted = int(dist_list[0]), int(dist_list[2])
                b_dist_landed, b_dist_atmpted = int(dist_list[3]), int(dist_list[5])
                r_dist_acc = (
                    int(round(r_dist_landed / r_dist_atmpted, 2) * 100)
                    if r_dist_atmpted > 0
                    else None
                )
                b_dist_acc = (
                    int(round(b_dist_landed / b_dist_atmpted, 2) * 100)
                    if b_dist_atmpted > 0
                    else None
                )

                clinch_list = td_2_list[7].text.split()
                r_clinch_landed, r_clinch_atmpted = (
                    int(clinch_list[0]),
                    int(clinch_list[2]),
                )
                b_clinch_landed, b_clinch_atmpted = (
                    int(clinch_list[3]),
                    int(clinch_list[5]),
                )
                r_clinch_acc = (
                    int(round(r_clinch_landed / r_clinch_atmpted, 2) * 100)
                    if r_clinch_atmpted > 0
                    else None
                )
                b_clinch_acc = (
                    int(round(b_clinch_landed / b_clinch_atmpted, 2) * 100)
                    if b_clinch_atmpted > 0
                    else None
                )

                ground_list = td_2_list[8].text.split()
                r_ground_landed, r_ground_atmpted = (
                    int(ground_list[0]),
                    int(ground_list[2]),
                )
                b_ground_landed, b_ground_atmpted = (
                    int(ground_list[3]),
                    int(ground_list[5]),
                )
                r_ground_acc = (
                    int(round(r_ground_landed / r_ground_atmpted, 2) * 100)
                    if r_ground_atmpted > 0
                    else None
                )
                b_ground_acc = (
                    int(round(b_ground_landed / b_ground_atmpted, 2) * 100)
                    if b_ground_atmpted > 0
                    else None
                )
            else:
                (
                    r_head_landed,
                    r_head_atmpted,
                    b_head_landed,
                    b_head_atmpted,
                    r_head_acc,
                    b_head_acc,
                ) = None, None, None, None, None, None
                (
                    r_body_landed,
                    r_body_atmpted,
                    b_body_landed,
                    b_body_atmpted,
                    r_body_acc,
                    b_body_acc,
                ) = None, None, None, None, None, None
                (
                    r_leg_landed,
                    r_leg_atmpted,
                    b_leg_landed,
                    b_leg_atmpted,
                    r_leg_acc,
                    b_leg_acc,
                ) = None, None, None, None, None, None
                (
                    r_dist_landed,
                    r_dist_atmpted,
                    b_dist_landed,
                    b_dist_atmpted,
                    r_dist_acc,
                    b_dist_acc,
                ) = None, None, None, None, None, None
                (
                    r_clinch_landed,
                    r_clinch_atmpted,
                    b_clinch_landed,
                    b_clinch_atmpted,
                    r_clinch_acc,
                    b_clinch_acc,
                ) = None, None, None, None, None, None
                (
                    r_ground_landed,
                    r_ground_atmpted,
                    b_ground_landed,
                    b_ground_atmpted,
                    r_ground_acc,
                    b_ground_acc,
                ) = None, None, None, None, None, None
        else:
            (
                r_kd,
                b_kd,
                r_sig_str_landed,
                r_sig_str_atmpted,
                b_sig_str_landed,
                b_sig_str_atmpted,
            ) = None, None, None, None, None, None
            (
                r_sig_str_acc,
                b_sig_str_acc,
                r_total_str_landed,
                r_total_str_atmpted,
                b_total_str_landed,
                b_total_str_atmpted,
            ) = None, None, None, None, None, None
            (
                r_total_str_acc,
                b_total_str_acc,
                r_td_landed,
                r_td_atmpted,
                b_td_landed,
                b_td_atmpted,
            ) = None, None, None, None, None, None
            r_td_acc, b_td_acc, r_sub_att, b_sub_att, r_rev, b_rev, r_ctrl, b_ctrl = (
                None,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            )
            (
                r_head_landed,
                r_head_atmpted,
                b_head_landed,
                b_head_atmpted,
                r_head_acc,
                b_head_acc,
            ) = None, None, None, None, None, None
            (
                r_body_landed,
                r_body_atmpted,
                b_body_landed,
                b_body_atmpted,
                r_body_acc,
                b_body_acc,
            ) = None, None, None, None, None, None
            (
                r_leg_landed,
                r_leg_atmpted,
                b_leg_landed,
                b_leg_atmpted,
                r_leg_acc,
                b_leg_acc,
            ) = None, None, None, None, None, None
            (
                r_dist_landed,
                r_dist_atmpted,
                b_dist_landed,
                b_dist_atmpted,
                r_dist_acc,
                b_dist_acc,
            ) = None, None, None, None, None, None
            (
                r_clinch_landed,
                r_clinch_atmpted,
                b_clinch_landed,
                b_clinch_atmpted,
                r_clinch_acc,
                b_clinch_acc,
            ) = None, None, None, None, None, None
            (
                r_ground_landed,
                r_ground_atmpted,
                b_ground_landed,
                b_ground_atmpted,
                r_ground_acc,
                b_ground_acc,
            ) = None, None, None, None, None, None

        # PARSE PERCENTAGES (HEAD/BODY/LEG/DIST/CLINCH/GROUND)
        r_landed_head_per, r_landed_dist_per, b_landed_head_per, b_landed_dist_per = (
            None,
            None,
            None,
            None,
        )
        try:
            r_list_hp = soup.find_all(
                "i",
                class_="b-fight-details__charts-num b-fight-details__charts-num_style_red b-fight-details__charts-num_pos_left js-red",
            )
            if len(r_list_hp) >= 2:
                r_landed_head_per = int(r_list_hp[0].text.strip().replace("%", ""))
                r_landed_dist_per = int(r_list_hp[1].text.strip().replace("%", ""))
            b_list_hp = soup.find_all(
                "i",
                class_="b-fight-details__charts-num b-fight-details__charts-num_style_blue b-fight-details__charts-num_pos_right js-blue",
            )
            if len(b_list_hp) >= 2:
                b_landed_head_per = int(b_list_hp[0].text.strip().replace("%", ""))
                b_landed_dist_per = int(b_list_hp[1].text.strip().replace("%", ""))
        except:
            pass

        (
            r_landed_body_per,
            r_landed_clinch_per,
            b_landed_body_per,
            b_landed_clinch_per,
        ) = None, None, None, None
        try:
            r_list_bp = soup.find_all(
                "i",
                class_="b-fight-details__charts-num b-fight-details__charts-num_style_dark-red b-fight-details__charts-num_pos_left js-red",
            )
            if len(r_list_bp) >= 2:
                r_landed_body_per = int(r_list_bp[0].text.strip().replace("%", ""))
                r_landed_clinch_per = int(r_list_bp[1].text.strip().replace("%", ""))
            b_list_bp = soup.find_all(
                "i",
                class_="b-fight-details__charts-num b-fight-details__charts-num_style_dark-blue b-fight-details__charts-num_pos_right js-blue",
            )
            if len(b_list_bp) >= 2:
                b_landed_body_per = int(b_list_bp[0].text.strip().replace("%", ""))
                b_landed_clinch_per = int(b_list_bp[1].text.strip().replace("%", ""))
        except:
            pass

        r_landed_leg_per, r_landed_ground_per, b_landed_leg_per, b_landed_ground_per = (
            None,
            None,
            None,
            None,
        )
        try:
            r_list_lp = soup.find_all(
                "i",
                class_="b-fight-details__charts-num b-fight-details__charts-num_style_light-red b-fight-details__charts-num_pos_left js-red",
            )
            if len(r_list_lp) >= 2:
                r_landed_leg_per = int(r_list_lp[0].text.strip().replace("%", ""))
                r_landed_ground_per = int(r_list_lp[1].text.strip().replace("%", ""))
            b_list_lp = soup.find_all(
                "i",
                class_="b-fight-details__charts-num b-fight-details__charts-num_style_light-blue b-fight-details__charts-num_pos_right js-blue",
            )
            if len(b_list_lp) >= 2:
                b_landed_leg_per = int(b_list_lp[0].text.strip().replace("%", ""))
                b_landed_ground_per = int(b_list_lp[1].text.strip().replace("%", ""))
        except:
            pass

        data_dic = {
            "event_name": event_name,
            "event_id": event_id,
            "fight_id": fight_id,
            "r_name": r_name,
            "r_id": r_id,
            "b_name": b_name,
            "b_id": b_id,
            "division": division_info,
            "title_fight": is_title_fight,
            "method": method,
            "finish_round": finish_round,
            "match_time_sec": match_time_sec,
            "total_rounds": total_rounds,
            "referee": referee,
            "r_kd": r_kd,
            "r_sig_str_landed": r_sig_str_landed,
            "r_sig_str_atmpted": r_sig_str_atmpted,
            "r_sig_str_acc": r_sig_str_acc,
            "r_total_str_landed": r_total_str_landed,
            "r_total_str_atmpted": r_total_str_atmpted,
            "r_total_str_acc": r_total_str_acc,
            "r_td_landed": r_td_landed,
            "r_td_atmpted": r_td_atmpted,
            "r_td_acc": r_td_acc,
            "r_sub_att": r_sub_att,
            "r_ctrl": r_ctrl,
            "r_head_landed": r_head_landed,
            "r_head_atmpted": r_head_atmpted,
            "r_head_acc": r_head_acc,
            "r_body_landed": r_body_landed,
            "r_body_atmpted": r_body_atmpted,
            "r_body_acc": r_body_acc,
            "r_leg_landed": r_leg_landed,
            "r_leg_atmpted": r_leg_atmpted,
            "r_leg_acc": r_leg_acc,
            "r_dist_landed": r_dist_landed,
            "r_dist_atmpted": r_dist_atmpted,
            "r_dist_acc": r_dist_acc,
            "r_clinch_landed": r_clinch_landed,
            "r_clinch_atmpted": r_clinch_atmpted,
            "r_clinch_acc": r_clinch_acc,
            "r_ground_landed": r_ground_landed,
            "r_ground_atmpted": r_ground_atmpted,
            "r_ground_acc": r_ground_acc,
            "r_landed_head_per": r_landed_head_per,
            "r_landed_body_per": r_landed_body_per,
            "r_landed_leg_per": r_landed_leg_per,
            "r_landed_dist_per": r_landed_dist_per,
            "r_landed_clinch_per": r_landed_clinch_per,
            "r_landed_ground_per": r_landed_ground_per,
            "b_kd": b_kd,
            "b_sig_str_landed": b_sig_str_landed,
            "b_sig_str_atmpted": b_sig_str_atmpted,
            "b_sig_str_acc": b_sig_str_acc,
            "b_total_str_landed": b_total_str_landed,
            "b_total_str_atmpted": b_total_str_atmpted,
            "b_total_str_acc": b_total_str_acc,
            "b_td_landed": b_td_landed,
            "b_td_atmpted": b_td_atmpted,
            "b_td_acc": b_td_acc,
            "b_sub_att": b_sub_att,
            "b_ctrl": b_ctrl,
            "b_head_landed": b_head_landed,
            "b_head_atmpted": b_head_atmpted,
            "b_head_acc": b_head_acc,
            "b_body_landed": b_body_landed,
            "b_body_atmpted": b_body_atmpted,
            "b_body_acc": b_body_acc,
            "b_leg_landed": b_leg_landed,
            "b_leg_atmpted": b_leg_atmpted,
            "b_leg_acc": b_leg_acc,
            "b_dist_landed": b_dist_landed,
            "b_dist_atmpted": b_dist_atmpted,
            "b_dist_acc": b_dist_acc,
            "b_clinch_landed": b_clinch_landed,
            "b_clinch_atmpted": b_clinch_atmpted,
            "b_clinch_acc": b_clinch_acc,
            "b_ground_landed": b_ground_landed,
            "b_ground_atmpted": b_ground_atmpted,
            "b_ground_acc": b_ground_acc,
            "b_landed_head_per": b_landed_head_per,
            "b_landed_body_per": b_landed_body_per,
            "b_landed_leg_per": b_landed_leg_per,
            "b_landed_dist_per": b_landed_dist_per,
            "b_landed_clinch_per": b_landed_clinch_per,
            "b_landed_ground_per": b_landed_ground_per,
        }
        fight_details.append(data_dic)


async def get_fighter_data(client, semaphore, idx, id):
    """Scrape fighter data from the given link, including physical stats, stance, and dob."""
    base_url = "http://ufcstats.com/fighter-details/"
    async with semaphore:
        html = await fetch_html(client, base_url + id)
        if not html:
            return

        soup = BeautifulSoup(html, "lxml")
        
        # --- NOME, APELIDO E CARTEL ---
        name_tag = soup.find("span", class_="b-content__title-highlight")
        fighter_name = name_tag.text.strip() if name_tag else None

        nickname_tag = soup.find("p", class_="b-content__Nickname")
        fighter_nick_name = nickname_tag.text.strip() if nickname_tag else None

        record_tag = soup.find("span", class_="b-content__title-record")
        if record_tag:
            fighter_record = record_tag.text.replace("Record:", "").strip().split("-")
            try:
                fighter_wins = int(fighter_record[0].split()[0])
                fighter_losses = int(fighter_record[1].split()[0])
                fighter_draws = int(fighter_record[2].split()[0])
            except:
                fighter_wins, fighter_losses, fighter_draws = 0, 0, 0
        else:
            fighter_wins, fighter_losses, fighter_draws = None, None, None

        # --- EXTRAÇÃO FÍSICA, BASE E IDADE ---
        fighter_height, fighter_weight, fighter_reach = None, None, None
        fighter_stance, fighter_dob = None, None
        
        info_list = soup.find_all("li", class_="b-list__box-list-item b-list__box-list-item_type_block")
        
        for item in info_list:
            title_tag = item.find("i", class_="b-list__box-item-title")
            if title_tag:
                title_text = title_tag.text.strip().lower()
                value = item.text.replace(title_tag.text, "").strip()
                
                if value == "" or value == "--":
                    value = None

                if "height" in title_text:
                    fighter_height = value
                elif "weight" in title_text:
                    fighter_weight = value
                elif "reach" in title_text:
                    fighter_reach = value
                elif "stance" in title_text:
                    fighter_stance = value
                elif "dob" in title_text:
                    fighter_dob = value

        # --- ADICIONA TUDO NO DICIONÁRIO ---
        data_dic = {
            "id": id,
            "name": fighter_name,
            "nick_name": fighter_nick_name,
            "height": fighter_height,
            "weight": fighter_weight,
            "reach": fighter_reach,
            "stance": fighter_stance, # Ex: Orthodox, Southpaw, Switch
            "dob": fighter_dob,       # Ex: Oct 17, 1989
            "wins": fighter_wins,
            "losses": fighter_losses,
            "draws": fighter_draws,
        }
        fighter_detail_data.append(data_dic)


async def main():
    print("Fetching event links...")
    ufc_link = "http://ufcstats.com/statistics/events/completed?page=all"

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    transport = httpx.AsyncHTTPTransport(retries=3)
    limits = httpx.Limits(
        max_connections=MAX_CONCURRENT_REQUESTS,
        max_keepalive_connections=MAX_CONCURRENT_REQUESTS,
    )

    async with httpx.AsyncClient(transport=transport, limits=limits) as client:
        html = await fetch_html(client, ufc_link)
        if not html:
            print("Failed to fetch initial events.")
            return

        soup = BeautifulSoup(html, "lxml")
        event_links_soup = soup.find_all("a", class_="b-link b-link_style_black")
        event_links = [link["href"] for link in event_links_soup]
        print(f"{len(event_links)} events found.")

        # 1. Scrape Events
        total_events = len(event_links)
        print(f"Scraping {total_events} event details...")
        tasks = [
            get_event_data(client, semaphore, idx, link)
            for idx, link in enumerate(event_links)
        ]
        completed = 0
        for task in asyncio.as_completed(tasks):
            await task
            completed += 1
            if completed % 50 == 0 or completed == total_events:
                print(f"Events scraped: {completed}/{total_events}")

        df_winner = pd.DataFrame(data=winner_names)
        df_winner.to_csv("datasets/event_details.csv", index=False)
        print(f"Successfully scraped {len(df_winner)} events.")

        # 2. Scrape Fights
        total_fights = len(new_fight_links_all)
        print(f"Scraping {total_fights} fight details...")
        tasks = [
            get_fight_data(client, semaphore, idx, link)
            for idx, link in enumerate(new_fight_links_all)
        ]
        completed = 0
        for task in asyncio.as_completed(tasks):
            await task
            completed += 1
            if completed % 500 == 0 or completed == total_fights:
                print(f"Fights scraped: {completed}/{total_fights}")

        df_fight = pd.DataFrame(data=fight_details)
        df_fight.to_csv("datasets/fight_details.csv", index=False)
        print(f"Successfully scraped {len(df_fight)} fights.")

        # 3. Scrape Fighters
        print("Scraping fighter details...")
        if (
            not df_fight.empty
            and "r_id" in df_fight.columns
            and "b_id" in df_fight.columns
        ):
            r_fighter_id = df_fight["r_id"].unique()
            b_fighter_id = df_fight["b_id"].unique()
            all_ids = list(set(list(r_fighter_id) + list(b_fighter_id)))
            total_fighters = len(all_ids)
            print(f"Found {total_fighters} unique fighters to scrape.")
            
            tasks = [
                get_fighter_data(client, semaphore, idx, id)
                for idx, id in enumerate(all_ids)
            ]
            completed = 0
            for task in asyncio.as_completed(tasks):
                await task
                completed += 1
                if completed % 200 == 0 or completed == total_fighters:
                    print(f"Fighters scraped: {completed}/{total_fighters}")

            df_fighter = pd.DataFrame(data=fighter_detail_data)
            df_fighter.to_csv("datasets/fighter_details.csv", index=False)
            print(f"Successfully scraped {len(df_fighter)} fighters.")

            # 4. Merge Data
            print("Merging datasets into UFC.csv...")
            df_merger_winners = df_winner.drop(columns=["event_id"]).copy()
            df_fight_final = df_fight.merge(right=df_merger_winners, on="fight_id")

            df_fighter_renamed__r = df_fighter.add_prefix("r_").drop(
                columns=["r_name"], errors="ignore"
            )
            df_fighter_renamed__b = df_fighter.add_prefix("b_").drop(
                columns=["b_name"], errors="ignore"
            )

            df_fight_final = df_fight_final.merge(
                right=df_fighter_renamed__r, left_on="r_id", right_on="r_id", how="left"
            )
            df_fight_final = df_fight_final.merge(
                right=df_fighter_renamed__b, left_on="b_id", right_on="b_id", how="left"
            )

            df_fight_final.to_csv("datasets/UFC.csv", index=False)
            print(
                "Scraping and merging complete. All data saved to datasets/ directory."
            )
        else:
            print("No fights found or missing columns. Skipping merge step.")


if __name__ == "__main__":
    asyncio.run(main())
