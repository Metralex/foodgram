import { Title, Container, Main } from '../../components'
import styles from './styles.module.css'
import MetaTags from 'react-meta-tags'

const About = ({ updateOrders, orders }) => {
  
  return <Main>
    <MetaTags>
      <title>О проекте</title>
      <meta name="description" content="Фудграм - О проекте" />
      <meta property="og:title" content="О проекте" />
    </MetaTags>
    
    <Container>
      <h1 className={styles.title}>Foodgram</h1>
      <div className={styles.content}>
        <div className={styles.text}>
          <p className={styles.textItem}>
            Foodgram — это веб-приложение для управления рецептами, позволяющее пользователям создавать, хранить и делиться рецептами, подписываться на авторов, добавлять рецепты в избранное и формировать списки покупок.
          </p>
          <p className={styles.textItem}>
            Код проекта - <a href="https://github.com/metralex/foodgram" className={styles.textLink} target="_blank" rel="noopener noreferrer">Github</a>
          </p>
          <p className={styles.textItem}>
            Автор: <a href="https://github.com/metralex" className={styles.textLink} target="_blank" rel="noopener noreferrer">metralex</a>
          </p>
        </div>
      </div>
      
    </Container>
  </Main>
}

export default About

