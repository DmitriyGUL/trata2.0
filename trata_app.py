import streamlit as st
import uuid
from datetime import datetime
import time

# Инициализация состояния
def init_session():
    defaults = {
        'groups': {},
        'expenses': {},
        'members': {},
        'current_group': None,
        'user_id': str(uuid.uuid4())[:8]
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

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

# Главное приложение
def main():
    st.set_page_config(
        page_title="Trata - Управление групповыми расходами",
        page_icon="💰",
        layout="centered",
        initial_sidebar_state="collapsed"
    )
    
    # Инициализация сессии
    init_session()
    
    # Минимальные CSS стили для совместимости
    st.markdown("""
    <style>
        /* Основной градиентный фон */
        .stApp {
            background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
            background-attachment: fixed;
            padding: 20px;
        }
        
        /* Карточки */
        .card {
            background: rgba(255, 255, 255, 0.92);
            border-radius: 20px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }
        
        /* Кнопки */
        .stButton>button {
            background: linear-gradient(to right, #6a11cb, #2575fc) !important;
            color: white !important;
            border-radius: 50px !important;
            padding: 10px 20px !important;
        }
        
        /* Заголовки */
        .stMarkdown h1 {
            color: white;
            text-align: center;
            margin-bottom: 30px;
        }
        
        /* Цвета для долгов */
        .debtor { color: #ff4757; font-weight: bold; }
        .creditor { color: #2ed573; font-weight: bold; }
        
        /* Мобильная адаптация */
        @media (max-width: 768px) {
            .stButton>button { width: 100%; }
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Главная страница - создание группы
    if st.session_state.current_group is None:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.title("💰 Trata")
        st.subheader("Управление групповыми расходами")
        
        with st.form("create_group_form"):
            group_name = st.text_input("Название компании", max_chars=50, placeholder="Введите название")
            col1, col2 = st.columns(2)
            with col1:
                create_btn = st.form_submit_button("Создать группу")
            with col2:
                join_btn = st.form_submit_button("Присоединиться")
                
            if create_btn and group_name:
                group_id = str(uuid.uuid4())
                st.session_state.groups[group_id] = {
                    'name': group_name,
                    'created_at': datetime.now().strftime("%Y-%m-%d %H:%M")
                }
                st.session_state.members[group_id] = [st.session_state.user_id]
                st.session_state.current_group = group_id
                st.experimental_rerun()
                
            if join_btn:
                st.session_state.show_join = True
                
        if st.session_state.get('show_join', False):
            with st.form("join_form"):
                group_id = st.text_input("ID группы", placeholder="Введите ID группы")
                if st.form_submit_button("Присоединиться"):
                    if group_id in st.session_state.groups:
                        st.session_state.current_group = group_id
                        if st.session_state.user_id not in st.session_state.members[group_id]:
                            st.session_state.members[group_id].append(st.session_state.user_id)
                        st.experimental_rerun()
                    else:
                        st.error("Группа не найдена")
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Страница группы
    else:
        group_id = st.session_state.current_group
        group = st.session_state.groups[group_id]
        members = st.session_state.members.get(group_id, [])
        expenses = st.session_state.expenses.get(group_id, [])
        
        # Шапка
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.title(group['name'])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("✚ Участник", use_container_width=True):
                st.session_state.show_add_member = True
        with col2:
            if st.button("✚ Трата", use_container_width=True):
                st.session_state.show_add_expense = True
        with col3:
            if st.button("← Назад", use_container_width=True):
                st.session_state.current_group = None
                st.experimental_rerun()
        
        # Участники
        st.subheader("Участники")
        if members:
            st.write(", ".join(members))
        else:
            st.info("Пока нет участников")
        
        # Форма добавления участника
        if st.session_state.get('show_add_member', False):
            with st.form("add_member_form"):
                new_member = st.text_input("Имя участника")
                if st.form_submit_button("Добавить"):
                    if new_member:
                        st.session_state.members[group_id].append(new_member)
                        st.success(f"Участник {new_member} добавлен!")
                        st.session_state.show_add_member = False
                        time.sleep(1)
                        st.experimental_rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Траты
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Траты")
        
        if expenses:
            for expense in expenses:
                st.markdown(f"""
                    <div style="
                        padding: 15px;
                        margin: 10px 0;
                        background: white;
                        border-radius: 10px;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    ">
                        <div><b>{expense['description']}</b></div>
                        <div>💳 Оплатил: {expense['payer']}</div>
                        <div style="color: #ff4757; font-weight: bold;">💸 {expense['amount']} ₽</div>
                        <div style="font-size: 0.8em; color: #666;">⏱ {expense['date']}</div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Пока нет трат")
        
        # Форма добавления траты
        if st.session_state.get('show_add_expense', False):
            with st.form("add_expense_form"):
                col1, col2 = st.columns(2)
                with col1:
                    description = st.text_input("Описание")
                with col2:
                    amount = st.number_input("Сумма", min_value=0.01, step=0.01)
                
                payer = st.selectbox("Кто оплатил?", members)
                
                if st.form_submit_button("Добавить трату"):
                    if description and amount:
                        new_expense = {
                            'id': str(uuid.uuid4()),
                            'description': description,
                            'amount': float(amount),
                            'payer': payer,
                            'date': datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                        st.session_state.expenses[group_id].append(new_expense)
                        st.success("Трата добавлена!")
                        time.sleep(1)
                        st.session_state.show_add_expense = False
                        st.experimental_rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Расчет долгов
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Расчет долгов")
        
        transactions = calculate_debts(group_id)
        if transactions:
            for t in transactions:
                st.markdown(f"""
                    <div style="
                        padding: 10px;
                        margin: 10px 0;
                        background: white;
                        border-radius: 10px;
                    ">
                        <span class="debtor">{t['from']}</span> → 
                        <span class="creditor">{t['to']}</span>: 
                        <b>{t['amount']} ₽</b>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Нет долгов для расчета")
        
        if st.button("🔄 Пересчитать долги", use_container_width=True):
            st.experimental_rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Приглашение
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Пригласить в группу")
        invite_code = f"ID группы: `{group_id}`"
        st.code(invite_code, language="text")
        st.info("Отправьте этот ID другим участникам")
        st.markdown("</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
