import streamlit as st
import uuid
import pandas as pd
import numpy as np
from datetime import datetime
import time

# Инициализация состояния сессии
def init_session():
    session_defaults = {
        'groups': {},
        'expenses': {},
        'members': {},
        'current_group': None,
        'user_id': str(uuid.uuid4())[:8]
    }
    
    for key, value in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Функция для расчета долгов
def calculate_debts(group_id):
    members = st.session_state.members.get(group_id, [])
    expenses = st.session_state.expenses.get(group_id, [])
    
    if not members or not expenses:
        return []
    
    total_expenses = sum(float(e['amount']) for e in expenses)
    per_person = total_expenses / len(members)
    
    balances = {m: -per_person for m in members}
    
    for e in expenses:
        if e['payer'] in balances:
            balances[e['payer']] += float(e['amount'])
    
    debtors = []
    creditors = []
    
    for member, balance in balances.items():
        if balance < -0.01:
            debtors.append({'member': member, 'amount': -balance})
        elif balance > 0.01:
            creditors.append({'member': member, 'amount': balance})
    
    debtors.sort(key=lambda x: x['amount'], reverse=True)
    creditors.sort(key=lambda x: x['amount'], reverse=True)
    
    transactions = []
    d_index = 0
    c_index = 0
    
    while d_index < len(debtors) and c_index < len(creditors):
        debtor = debtors[d_index]
        creditor = creditors[c_index]
        amount = min(debtor['amount'], creditor['amount'])
        
        transactions.append({
            'from': debtor['member'],
            'to': creditor['member'],
            'amount': round(amount, 2)
        })
        
        debtor['amount'] -= amount
        creditor['amount'] -= amount
        
        if debtor['amount'] < 0.01:
            d_index += 1
        if creditor['amount'] < 0.01:
            c_index += 1
    
    return transactions

# Функция для показа уведомлений
def show_notification(message):
    notification = st.empty()
    notification.success(message)
    time.sleep(2)
    notification.empty()

# Главная функция
def main():
    st.set_page_config(
        page_title="Trata - Управление групповыми расходами",
        page_icon="💰",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    init_session()
    
    # CSS стили
    st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
            background-attachment: fixed;
            min-height: 100vh;
            padding: 2rem;
        }
        .stButton>button {
            background: linear-gradient(to right, #6a11cb, #2575fc) !important;
            color: white !important;
            border: none !important;
            border-radius: 50px !important;
            padding: 10px 20px !important;
            font-weight: 600 !important;
            box-shadow: 0 4px 15px rgba(106, 17, 203, 0.3) !important;
            transition: all 0.3s !important;
        }
        .stButton>button:hover {
            transform: translateY(-3px) !important;
            box-shadow: 0 7px 20px rgba(106, 17, 203, 0.4) !important;
        }
        .stTextInput>div>div>input, 
        .stNumberInput>div>div>input, 
        .stSelectbox>div>div>select {
            border-radius: 50px !important;
            padding: 10px 15px !important;
            border: 2px solid #ddd !important;
        }
        .stTextInput>div>div>input:focus, 
        .stNumberInput>div>div>input:focus, 
        .stSelectbox>div>div>select:focus {
            border-color: #6a11cb !important;
            box-shadow: 0 0 0 3px rgba(106, 17, 203, 0.2) !important;
        }
        .card {
            background: rgba(255, 255, 255, 0.92) !important;
            border-radius: 20px !important;
            padding: 25px !important;
            margin-bottom: 20px !important;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2) !important;
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 15px;
        }
        .debtor {
            color: #ff4757;
            font-weight: 600;
        }
        .creditor {
            color: #2ed573;
            font-weight: 600;
        }
        .amount-badge {
            background: linear-gradient(45deg, #6a11cb, #2575fc);
            color: white;
            padding: 2px 10px;
            border-radius: 20px;
            font-weight: 600;
        }
        .member-tag {
            background: linear-gradient(45deg, #6a11cb, #2575fc);
            color: white;
            padding: 8px 15px;
            border-radius: 50px;
            display: inline-flex;
            align-items: center;
            margin: 5px;
            font-size: 14px;
        }
        .expense-item {
            padding: 15px;
            margin: 10px 0;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .logo-container {
            text-align: center;
            margin-bottom: 30px;
        }
        .logo {
            width: 140px;
            height: 140px;
            background: linear-gradient(45deg, #6a11cb, #2575fc);
            border-radius: 50%;
            margin: 0 auto 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 50px;
            color: white;
            font-weight: bold;
        }
        @media (max-width: 768px) {
            .header {
                flex-direction: column;
                align-items: flex-start;
            }
            .stButton>button {
                width: 100%;
            }
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Главная страница - создание группы
    if st.session_state.current_group is None:
        st.markdown("<div class='logo-container'>", unsafe_allow_html=True)
        st.markdown("<div class='logo'>💰</div>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; color: white;'>Trata</h1>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.title("Создайте новую компанию")
        
        group_name = st.text_input("Введите название компании", max_chars=50, placeholder="Название компании")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Создать группу", use_container_width=True, key="create_group_btn"):
                if group_name:
                    group_id = str(uuid.uuid4())
                    st.session_state.groups[group_id] = {
                        'name': group_name,
                        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M"),
                        'creator': st.session_state.user_id
                    }
                    st.session_state.expenses[group_id] = []
                    st.session_state.members[group_id] = [st.session_state.user_id]
                    st.session_state.current_group = group_id
                    st.experimental_rerun()
                else:
                    st.error("Введите название компании!")
        
        with col2:
            if st.button("Присоединиться к группе", use_container_width=True, key="join_group_btn"):
                st.session_state.show_join = True
                
        if st.session_state.get('show_join', False):
            group_id = st.text_input("Введите ID группы", placeholder="ID группы")
            if st.button("Присоединиться", use_container_width=True, key="join_btn"):
                if group_id and group_id in st.session_state.groups:
                    st.session_state.current_group = group_id
                    if st.session_state.user_id not in st.session_state.members[group_id]:
                        st.session_state.members[group_id].append(st.session_state.user_id)
                    st.experimental_rerun()
                else:
                    st.error("Группа с таким ID не найдена!")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Страница группы
    else:
        group_id = st.session_state.current_group
        group = st.session_state.groups[group_id]
        
        # Шапка
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("<div class='header'>", unsafe_allow_html=True)
        st.title(group['name'])
        
        # Кнопки управления группой
        col1, col2, col3 = st.columns([2,2,1])
        with col1:
            if st.button("Добавить участника", key="add_member_btn"):
                st.session_state.show_add_member = True
        with col2:
            if st.button("Добавить трату", key="add_expense_btn"):
                st.session_state.show_add_expense = True
        with col3:
            if st.button("← На главную", key="back_btn"):
                st.session_state.current_group = None
                st.experimental_rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Отображение участников
        st.subheader("Участники")
        members = st.session_state.members.get(group_id, [])
        if members:
            members_html = "<div style='display: flex; flex-wrap: wrap; margin-bottom: 20px;'>"
            for member in members:
                members_html += f"<div class='member-tag'>{member}</div>"
            members_html += "</div>"
            st.markdown(members_html, unsafe_allow_html=True)
        else:
            st.info("Пока нет участников")
        
        # Форма добавления участника
        if st.session_state.get('show_add_member', False):
            with st.form("add_member_form"):
                new_member = st.text_input("Имя участника", key="new_member_name")
                submit = st.form_submit_button("Добавить")
                if submit:
                    if new_member:
                        if new_member not in members:
                            st.session_state.members[group_id].append(new_member)
                            show_notification(f"Участник {new_member} добавлен!")
                            st.session_state.show_add_member = False
                            st.experimental_rerun()
                        else:
                            st.error("Участник уже в группе")
                    else:
                        st.error("Введите имя участника")
        
        st.markdown("</div>", unsafe_allow_html=True)  # Закрываем карточку
        
        # Секция трат
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Траты")
        
        expenses = st.session_state.expenses.get(group_id, [])
        if expenses:
            for expense in expenses:
                st.markdown(f"""
                    <div class="expense-item">
                        <div><b>{expense['description']}</b></div>
                        <div>Оплатил: {expense['payer']}</div>
                        <div style="color: #ff4757; font-weight: bold;">{expense['amount']} ₽</div>
                        <div style="font-size: 0.8em; color: #666;">{expense['date']}</div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Пока нет трат")
        
        # Форма добавления траты
        if st.session_state.get('show_add_expense', False):
            with st.form("add_expense_form"):
                col1, col2, col3 = st.columns([3, 2, 2])
                with col1:
                    expense_desc = st.text_input("Описание траты", key="expense_desc")
                with col2:
                    expense_amount = st.number_input("Сумма", min_value=0.01, step=0.01, format="%.2f", key="expense_amount")
                with col3:
                    payer = st.selectbox("Кто оплатил?", members, key="payer_select")
                
                submit = st.form_submit_button("Добавить трату")
                if submit:
                    if expense_desc and expense_amount:
                        new_expense = {
                            'id': str(uuid.uuid4()),
                            'description': expense_desc,
                            'amount': float(expense_amount),
                            'payer': payer,
                            'date': datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                        st.session_state.expenses[group_id].append(new_expense)
                        show_notification("Трата добавлена!")
                        st.session_state.show_add_expense = False
                        st.experimental_rerun()
                    else:
                        st.error("Заполните описание и сумму")
        
        st.markdown("</div>", unsafe_allow_html=True)  # Закрываем карточку
        
        # Секция расчета долгов
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Расчет долгов")
        
        transactions = calculate_debts(group_id)
        if transactions:
            st.markdown("**Для погашения долгов:**")
            for t in transactions:
                st.markdown(f"""
                    <div style="
                        padding: 10px;
                        margin: 10px 0;
                        background: white;
                        border-radius: 10px;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    ">
                        <span class="debtor">{t['from']}</span> должен 
                        <span class="creditor">{t['to']}</span>
                        <span class="amount-badge">{t['amount']} ₽</span>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Нет долгов для расчета или недостаточно данных")
        
        if st.button("Пересчитать долги", key="recalculate_debts"):
            st.experimental_rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)  # Закрываем карточку
        
        # Пригласительная ссылка
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Пригласить в группу")
        
        invite_url = f"https://share.streamlit.io/{YOUR_USERNAME}/{YOUR_REPO}/trata_app.py?group_id={group_id}&user_id={st.session_state.user_id}"
        st.code(invite_url, language="text")
        
        if st.button("Скопировать ссылку", key="copy_invite"):
            st.session_state.copied = True
            st.experimental_rerun()
        
        if st.session_state.get('copied', False):
            st.success("Ссылка скопирована в буфер обмена!")
            st.session_state.copied = False
            
        st.markdown("</div>", unsafe_allow_html=True)  # Закрываем карточку

if __name__ == "__main__":
    main()
