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
            Код проекта - <a href="https://github.com/metralex/foodgram" className={styles.textLink}>Github</a>
          </p>
          <p className={styles.textItem}>
            Автор: <a href="https://github.com/metralex" className={styles.textLink}>metralex</a>
          </p>
        </div>
      </div>
      
    </Container>
  </Main>
}

export default About

